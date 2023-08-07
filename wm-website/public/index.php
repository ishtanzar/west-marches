<?php

use Dflydev\FigCookies\Cookies;
use Dflydev\FigCookies\FigResponseCookies;
use Elastic\Elasticsearch\ClientBuilder;
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

$config = new App\Config();
$user = new App\User();

$app = AppFactory::create();
$twig = Twig::create(__DIR__ . '/../views', [
//    'cache' => '/var/cache/wm-portal/twig'
]);

$twig['user'] = $user;
$twig['config'] = $config;

$app->addErrorMiddleware(true, true, true);
$app->add(new SessionMiddleware());
$app->add(TwigMiddleware::create($app, $twig));

$config->jwt_key = InMemory::plainText(getenv('JWT_SHARED_KEY'));
$config->apiKey = getenv('ADMIN_KEY');
$config->api_endpoint = getenv('API_ENDPOINT');
$config->play_endpoint = getenv('PLAY_ENDPOINT');
$config->web_root = getenv('WEB_ROOT');
$config->jwt_algorithm = new Sha256();

$es = ClientBuilder::create()
    ->setHosts(['elasticsearch:9200'])
    ->build();

$app->group('', function (RouteCollectorProxy $group) use ($app, $user, $config, $es) {
    // Home
    $group->get('/', function (Request $request, Response $response) use ($es) {
        $view = Twig::fromRequest($request);

        $es_resp = $es->get([
            'index' => 'kanka_note',
            'id' => '1729087'
        ]);

        return $view->render($response, 'index.html', [
            'content' => $es_resp['_source']['child']['entry_parsed']
        ]);
    });

    $group->group('', function (RouteCollectorProxy $group) use ($user, $es) {
        // Map
        $group->get('/map', function (Request $request, Response $response) {
            $view = Twig::fromRequest($request);

            return $view->render($response, 'map.html');
        });

        $group->get('/search', function (Request $request, Response $response) use ($user, $es) {
            if(!$user->isGM()) {
                throw new \Slim\Exception\HttpNotFoundException($request);
            }

            $view = Twig::fromRequest($request);
            $query = $request->getQueryParams()['q'] ?? '';

            $fields = ["name^5", "*.name^3", "child.entry"];

            if($user->foundry['role'] ?? 0 === 4) {
                $fields[] = '*';
            }

            $es_resp = $es->search([
                'index' => 'kanka_*',
                'body' => [
                    'query' => [
                        'query_string' => [
                            'query' => $query,
                            'fields' => $fields,
                        ]
                    ],
//                    'highlight' => [
//                        'boundary_scanner_locale' => 'fr-FR',
//                        'fields' => [
//                            '*.*' => (object) []
//                        ]
//                    ],
                    'size' => 50
                ]
            ]);

            $results = [];
            foreach($es_resp['hits']['hits'] as $hit) {
                $type = $hit['_source']['type'];

                $type = $hit['_source']['child']['type'] == 'Rapport-MJ' ? 'session_report' : $type;
                $results[$type][] = $hit['_source'];
            }

            if(isset($results['session_report'])) {
                uasort($results['session_report'], function ($a, $b) {
                    $a_year = $a['child']['calendar_year'];
                    $a_month = $a['child']['calendar_month'];
                    $a_day = $a['child']['calendar_day'];

                    $b_year = $b['child']['calendar_year'];
                    $b_month = $b['child']['calendar_month'];
                    $b_day = $b['child']['calendar_day'];

                    if($a_year == $b_year) {
                        if($a_month == $b_month) {
                            if($a_day == $b_day) {
                                return 0;
                            } else {
                                return $a_day - $b_day;
                            }
                        } else {
                            return $a_month - $b_month;
                        }
                    } else {
                        return $a_year - $b_year;
                    }
                });
            }

            return $view->render($response, 'search.html', [
                'q' => $query,
                'results' => $results
            ]);
        });

        // Account
        $group->get('/me', function (Request $request, Response $response) use ($user) {
            $view = Twig::fromRequest($request);

            return $view->render($response, 'account.html');
        });
    })->add(function (Request $request, RequestHandler $handler) use ($app, $user, $config) {
        // Enforce authentication
        if ($user->authenticated) {
            return $handler->handle($request);
        }

        return $app->getResponseFactory()->createResponse(302)
            ->withHeader('Location', (string) (new Uri($config->api_endpoint.'/oauth/discord'))
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

            $guzzle = new \GuzzleHttp\Client([
                \GuzzleHttp\RequestOptions::VERIFY => '/opt/project/wm-infra/deploy/local/rootCA.pem'
            ]);
            $api_response = $guzzle->get($config->api_endpoint.'/users/'.$user->id, [
                'headers' => [
                    'Authorization' => 'ApiKey-v1 '.$config->apiKey
                ]
            ]);

            if($api_response->getStatusCode() == 200) {
                $api_user = json_decode($api_response->getBody(), true);

                $user->discord = $api_user['discord'] ?? [];
                $user->kanka = $api_user['kanka'] ?? [];
                $user->oauth = $api_user['oauth'] ?? [];
                $user->foundry = $api_user['foundry'] ?? [];
            }

        } catch(RequiredConstraintsViolated $e) {
            $response = $app->getResponseFactory()->createResponse(302)
                ->withHeader('Location', (string) (new Uri($config->api_endpoint.'/oauth/discord'))
                    ->withQuery((string)Query::createFromParams(['redirect_uri' => (string)$request->getUri()]))
                );

            return FigResponseCookies::expire($response, JWT_COOKIE_NAME);
        }
    }

    return $handler->handle($request);
});

$app->run();