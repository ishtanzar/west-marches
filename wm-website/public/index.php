<?php

use Dflydev\FigCookies\Cookies;
use Dflydev\FigCookies\FigResponseCookies;
use Dflydev\FigCookies\Modifier\SameSite;
use Dflydev\FigCookies\SetCookie;
use GuzzleHttp\Psr7\Uri;
use GuzzleHttp\Psr7\UriComparator;
use Lcobucci\JWT\Encoding\ChainedFormatter;
use Lcobucci\JWT\Encoding\JoseEncoder;
use Lcobucci\JWT\Signer\Key\InMemory;
use Lcobucci\JWT\Signer\Rsa\Sha256;
use Lcobucci\JWT\Token\Builder;
use Lcobucci\JWT\Token\Parser;
use League\OAuth2\Client\Provider\AbstractProvider;
use League\OAuth2\Client\Provider\Exception\IdentityProviderException;
use League\OAuth2\Client\Provider\GenericProvider;
use League\Uri\Components\Query;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\RequestHandlerInterface as RequestHandler;
use Slim\Exception\HttpUnauthorizedException;
use Slim\Factory\AppFactory;
use Slim\Interfaces\RouteResolverInterface;
use Slim\Middleware\Session as SessionMiddleware;
use Slim\Routing\RouteCollectorProxy;
use Slim\Routing\RoutingResults;
use Slim\Views\Twig;
use Slim\Views\TwigMiddleware;
use SlimSession\Helper as SessionHelper;
use Wohali\OAuth2\Client\Provider\Discord as DiscordProvider;

require __DIR__ . '/../vendor/autoload.php';

const DISCORD_ACCESS_TOKEN_SESSION_KEY = 'discordAccessToken';
const DISCORD_ACCESS_TOKEN_JWT_KEY = 'discordAccessToken';

const KANKA_ACCESS_TOKEN_SESSION_KEY = 'kankaAccessToken';
const KANKA_ACCESS_TOKEN_JWT_KEY = 'kankaAccessToken';
const JWT_COOKIE_NAME = 'jwt';

$app = AppFactory::create();
$twig = Twig::create(__DIR__ . '/../views', [
//    'cache' => '/var/cache/wm-portal/twig'
]);

$app->addErrorMiddleware(true, true, true);
$app->add(new SessionMiddleware());
$app->add(TwigMiddleware::create($app, $twig));

$discordOAuth = new DiscordProvider([
    'clientId' => getenv('DISCORD_OAUTH_CLIENT'),
    'clientSecret' => getenv('DISCORD_OAUTH_SECRET'),
    'redirectUri' => getenv('DISCORD_OAUTH_REDIRECT')
]);

$kankaOAuth = new GenericProvider([
    'clientId' => '79',
    'clientSecret' => 'Iz5KpksGGPAOaE8Z6OogIdH2HgdzmGxxkm7tmlCe',
    'urlAuthorize' => 'https://kanka.io/oauth/authorize',
    'urlAccessToken' => 'https://kanka.io/oauth/token',
    'urlResourceOwnerDetails' => 'https://kanka.io/api/1.0/profile',
    'redirectUri' => getenv('KANKA_OAUTH_REDIRECT')
]);

$jwtKey = InMemory::file(getenv('JWT_CERTIFICATE'));

class JwtContent {
    public string $kankaToken = '';
    public string $discordToken = '';

    public function __toArray(): array
    {
        $result = [];

        if($this->kankaToken) $result[KANKA_ACCESS_TOKEN_JWT_KEY] = $this->kankaToken;
        if($this->discordToken) $result[DISCORD_ACCESS_TOKEN_JWT_KEY] = $this->discordToken;

        return $result;
    }
}

$jwtContent = new JwtContent();

class OAuthOptions {
    public AbstractProvider $provider;
    public RouteResolverInterface $routeResolver;
    public string $sessionStateKey = "oauth2state";
    public string $sessionRedirectKey = "oauth2redirectUri";
    public string $sessionTokenKey = "oauth2accessToken";
    public string $queryRedirectKey = "redirect_uri";

    /**
     * @param AbstractProvider $provider
     * @param RouteResolverInterface $routeResolver
     * @param string|null $sessionStateKey
     * @param string|null $sessionRedirectKey
     * @param string|null $sessionTokenKey
     * @param string|null $queryRedirectKey
     */
    public function __construct(AbstractProvider $provider, RouteResolverInterface $routeResolver,
                                string $sessionStateKey = null, string $sessionRedirectKey = null,
                                string $sessionTokenKey = null, string $queryRedirectKey = null)
    {
        $this->provider = $provider;
        $this->routeResolver = $routeResolver;
        $this->sessionStateKey = $sessionStateKey ?: $this->sessionStateKey;
        $this->sessionRedirectKey = $sessionRedirectKey ?: $this->sessionRedirectKey;
        $this->sessionTokenKey = $sessionTokenKey ?: $this->sessionTokenKey;
        $this->queryRedirectKey = $queryRedirectKey ?: $this->queryRedirectKey;
    }


}

/**
 * @param Request $request
 * @param Response $response
 * @param OAuthOptions $options
 * @return Response
 */
function performOAuth(Request $request, Response $response, OAuthOptions $options): Response {
    $session = new SessionHelper();
    $query = Query::createFromUri($request->getUri());
    if ($code = $query->get('code')) {
        $sessionState = $session->get($options->sessionStateKey, false);
        $session->delete($options->sessionStateKey);

        if ($query->get('state') !== $sessionState) {
            throw new HttpUnauthorizedException($request);
        }

        try {
            $session->set($options->sessionTokenKey, $options->provider->getAccessToken('authorization_code', [
                'code' => $code
            ]));

            return $response->withHeader('Location', $session->get($options->sessionRedirectKey, '/'))
                ->withStatus(302);
        } catch (IdentityProviderException $e) {
            throw new HttpUnauthorizedException($request, null, $e);
        }

    } else {
        // Only store the redirect_uri if it matches an existing route
        if ($uriString = $query->get($options->queryRedirectKey)) {
            $redirectUri = new Uri($uriString);

            if ((!UriComparator::isCrossOrigin($request->getUri(), $redirectUri)) &&
                $options->routeResolver->computeRoutingResults($redirectUri->getPath(), 'GET')
                    ->getRouteStatus() === RoutingResults::FOUND) {
                $session->set($options->sessionRedirectKey, $query->get($options->queryRedirectKey));
            }
        }

        // Redirect to Kanka OAuth page
        $url = $options->provider->getAuthorizationUrl([
            'redirect_uri' => (string) $request->getUri()->withQuery('')
        ]);
        $session->set($options->sessionStateKey, $options->provider->getState());

        return $response->withHeader('Location', $url)->withStatus(302);
    }
}

// Authenticated routes
$app->group('', function (RouteCollectorProxy $group) {
    // Home
    $group->get('/', function (Request $request, Response $response) {
        $view = Twig::fromRequest($request);

        return $view->render($response, 'index.html', []);
    });

    // Map
    $group->get('/map', function (Request $request, Response $response) {
        $view = Twig::fromRequest($request);

        return $view->render($response, 'map.html', []);
    });
})->add(function (Request $request, RequestHandler $handler) use ($jwtKey, $jwtContent) {
    // Send JWT
    $builder = new Builder(new JoseEncoder(), ChainedFormatter::default());
    $algorithm = new Sha256();
    $now = new DateTimeImmutable();

    $token = $builder
        ->issuedBy('http://westmarches.localhost.lan')
        ->permittedFor('http://westmarches.localhost.lan')
        ->identifiedBy('zeropziuqsdlkj')
        ->issuedAt($now)
        ->canOnlyBeUsedAfter($now)
        ->expiresAt($now->modify('+1 hour'));

    $response = $handler->handle($request);

    foreach ($jwtContent->__toArray() as $key => $value) {
        $token->withClaim($key, $value);
    }

    return FigResponseCookies::set($response, SetCookie::create(JWT_COOKIE_NAME)
        ->withValue($token->getToken($algorithm, $jwtKey)->toString())
        ->withDomain($request->getUri()->getHost())
        ->withSameSite(SameSite::lax())
    );
})->add(function (Request $request, RequestHandler $handler) use ($twig, $jwtContent) {
    // Kanka authentication middleware
    $session = new SessionHelper();

    $twig['kankaLoggedIn'] = false;

    if($session->exists(KANKA_ACCESS_TOKEN_SESSION_KEY)) {
        $jwtContent->kankaToken = $session->get(KANKA_ACCESS_TOKEN_SESSION_KEY);
        $twig['kankaLoggedIn'] = true;
    }

    return $handler->handle($request);
})->add(function (Request $request, RequestHandler $handler) use ($app, $jwtContent) {
    // Authentication middleware
    $session = new SessionHelper();

    if ($session->exists(DISCORD_ACCESS_TOKEN_SESSION_KEY)) {
        $jwtContent->discordToken = $session->get(DISCORD_ACCESS_TOKEN_SESSION_KEY);
        return $handler->handle($request);
    }

    return $app->getResponseFactory()->createResponse(302)
        ->withHeader('Location', (string)$request->getUri()
            ->withPath('/login')
            ->withQuery((string) Query::createFromParams(['redirect_uri' => (string) $request->getUri()]))
        );
})->add(function (Request $request, RequestHandler $handler) use ($jwtContent) {
    // Existing JWT cookie
    $session = new SessionHelper();
    $cookies = Cookies::fromRequest($request);

    if($cookies->has(JWT_COOKIE_NAME)) {
        $parser = new Parser(new JoseEncoder());
        /** @var \Lcobucci\JWT\Token\Plain $token */
        $token = $parser->parse($cookies->get(JWT_COOKIE_NAME)->getValue());

        if($token->claims()->has(KANKA_ACCESS_TOKEN_JWT_KEY)) {
            $session->set(KANKA_ACCESS_TOKEN_SESSION_KEY, $token->claims()->get(KANKA_ACCESS_TOKEN_JWT_KEY));
        }

        if($token->claims()->has(DISCORD_ACCESS_TOKEN_JWT_KEY)) {
            $session->set(DISCORD_ACCESS_TOKEN_SESSION_KEY, $token->claims()->get(DISCORD_ACCESS_TOKEN_JWT_KEY));
        }
    }

    return $handler->handle($request);
});

$app->get('/oauth/kanka', function (Request $request, Response $response) use ($kankaOAuth, $app) {
    return performOAuth($request, $response, new OAuthOptions(
        $kankaOAuth,
        $app->getRouteResolver(),
        'kankaOAuthState',
        'kankaRedirectUri',
        KANKA_ACCESS_TOKEN_SESSION_KEY));
});

$app->get('/login', function (Request $request, Response $response) use ($discordOAuth, $app) {
    return performOAuth($request, $response, new OAuthOptions(
        $discordOAuth,
        $app->getRouteResolver(),
        'discordOAuthState',
        'discordRedirectUri',
        DISCORD_ACCESS_TOKEN_SESSION_KEY));
});

$app->run();