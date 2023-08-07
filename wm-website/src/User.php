<?php

namespace App;

class User {
    public bool $authenticated = false;
    public string $id;
    public array $discord = [];
    public array $kanka = [];
    public array $oauth = [];
    public array $foundry = [];

    public function isGM() {
        return ($this->foundry['role'] ?? 0) == 4;
    }
}
