<?php

use Dflydev\FigCookies\Cookies;
use Dflydev\FigCookies\FigResponseCookies;
use GuzzleHttp\Psr7\Uri;
use Lcobucci\Clock\SystemClock;
use Lcobucci\JWT\Encoding\JoseEncoder;
use Lcobucci\JWT\Signer\Hmac\Sha256;
use Lcobucci\JWT\Signer\Key\InMemory;
use Lcobucci\JWT\Token\Parser;
use Lcobucci\JWT\Validation\Constraint\SignedWith;
use Lcobucci\JWT\Validation\Constraint\ValidAt;
use Lcobucci\JWT\Validation\RequiredConstraintsViolated;
use Lcobucci\JWT\Validation\Validator;
use League\Uri\Components\Query;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\RequestHandlerInterface as RequestHandler;
use Slim\Factory\AppFactory;
use Slim\Middleware\Session as SessionMiddleware;
use Slim\Routing\RouteCollectorProxy;
use Slim\Views\Twig;
use Slim\Views\TwigMiddleware;

require __DIR__ . '/../vendor/autoload.php';

const KANKA_ACCESS_TOKEN_SESSION_KEY = 'kankaAccessToken';
const JWT_COOKIE_NAME = 'access_token';

class User {
    public bool $authenticated = false;
    public string $id;
    public array $discord = [];
    public array $kanka = [];
    public array $oauth = [];
}

class Config {
    public string $apiKey;
    public \Lcobucci\JWT\Signer $jwt_algorithm;
    public \Lcobucci\JWT\Signer\Key $jwt_key;
}

$config = new Config();
$user = new User();

$app = AppFactory::create();
$twig = Twig::create(__DIR__ . '/../views', [
//    'cache' => '/var/cache/wm-portal/twig'
]);

$twig['user'] = $user;

$app->addErrorMiddleware(true, true, true);
$app->add(new SessionMiddleware());
$app->add(TwigMiddleware::create($app, $twig));

$config->jwt_key = InMemory::plainText(getenv('JWT_SHARED_KEY'));
$config->apiKey = getenv('ADMIN_KEY');
$config->jwt_algorithm = new Sha256();

$app->group('', function (RouteCollectorProxy $group) use ($app, $user, $config) {
    // Home
    $group->get('/', function (Request $request, Response $response) {
        $view = Twig::fromRequest($request);

        return $view->render($response, 'index.html', []);
    });

    $group->group('', function (RouteCollectorProxy $group) use ($user) {
        // Map
        $group->get('/map', function (Request $request, Response $response) {
            $view = Twig::fromRequest($request);

            return $view->render($response, 'map.html', []);
        });

        // Account
        $group->get('/me', function (Request $request, Response $response) use ($user) {
            $view = Twig::fromRequest($request);

            return $view->render($response, 'account.html', [
                'kanka_username' => $user->kanka['name']
            ]);
        });
    })->add(function (Request $request, RequestHandler $handler) use ($app, $user) {
        // Enforce authentication
        if ($user->authenticated) {
            return $handler->handle($request);
        }

        return $app->getResponseFactory()->createResponse(302)
            ->withHeader('Location', (string) (new Uri('https://api.westmarches.localhost.lan:8443/oauth/discord'))
                ->withQuery((string)Query::createFromParams(['redirect_uri' => (string)$request->getUri()]))
            );
    });
})->add(function (Request $request, RequestHandler $handler) use ($app, $user, $config) {
    // Existing JWT cookie
    $cookies = Cookies::fromRequest($request);

    if($cookies->has(JWT_COOKIE_NAME)) {
        $parser = new Parser(new JoseEncoder());
        /** @var \Lcobucci\JWT\Token\Plain $token */
        $token = $parser->parse($cookies->get(JWT_COOKIE_NAME)->getValue());

        $validator = new Validator();

        try {
            $validator->assert(
                $token,
                new SignedWith($config->jwt_algorithm, $config->jwt_key),
                new ValidAt(new SystemClock(new DateTimeZone(date_default_timezone_get()))),
            );

            $user->authenticated = true;
            $user->id = $token->claims()->get('user_id');

            $guzzle = new \GuzzleHttp\Client();
            $api_response = $guzzle->get("http://api:3000/users/".$user->id, [
                'headers' => [
                    'Authorization' => 'ApiKey-v1 '.$config->apiKey
                ]
            ]);

            if($api_response->getStatusCode() == 200) {
                $api_user = json_decode($api_response->getBody(), true);

                $user->discord = $api_user['discord'] ?? [];
                $user->kanka = $api_user['kanka'] ?? [];
                $user->oauth = $api_user['oauth'] ?? [];
            }

        } catch(RequiredConstraintsViolated $e) {
            $response = $app->getResponseFactory()->createResponse(302)
                ->withHeader('Location', (string) (new Uri('https://api.westmarches.localhost.lan:8443/oauth/discord'))
                    ->withQuery((string)Query::createFromParams(['redirect_uri' => (string)$request->getUri()]))
                );

            return FigResponseCookies::expire($response, JWT_COOKIE_NAME);
        }
    }

    return $handler->handle($request);
});

$app->run();