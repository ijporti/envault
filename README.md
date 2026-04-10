# envault

> A CLI tool for managing and encrypting environment variables across multiple projects and environments.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envault
```

---

## Usage

Initialize a vault for your project:

```bash
envault init
```

Add and encrypt an environment variable:

```bash
envault set MY_PROJECT production API_KEY "super-secret-value"
```

Retrieve and decrypt a variable:

```bash
envault get MY_PROJECT production API_KEY
```

Export all variables for an environment to a `.env` file:

```bash
envault export MY_PROJECT production > .env
```

List all tracked projects and environments:

```bash
envault list
```

---

## How It Works

`envault` stores encrypted environment variables in a local vault file (`~/.envault/vault.enc`). Variables are encrypted using AES-256 and protected by a master password. Each project can have multiple named environments (e.g., `development`, `staging`, `production`).

---

## Requirements

- Python 3.8+
- `cryptography` library (installed automatically)

---

## License

This project is licensed under the [MIT License](LICENSE).