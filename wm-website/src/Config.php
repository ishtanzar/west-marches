<?php

namespace App;

class Config {
    public string $apiKey;
    public string $api_endpoint;
    public string $play_endpoint;
    public string $web_root;
    public \Lcobucci\JWT\Signer $jwt_algorithm;
    public \Lcobucci\JWT\Signer\Key $jwt_key;
}
