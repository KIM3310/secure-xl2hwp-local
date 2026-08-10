from __future__ import annotations

import argparse
import hashlib
import secrets

PBKDF2_SCHEME = "pbkdf2_sha256"
PBKDF2_MIN_ITERATIONS = 390_000
PBKDF2_DEFAULT_ITERATIONS = PBKDF2_MIN_ITERATIONS
PBKDF2_MAX_ITERATIONS = 2_000_000
PBKDF2_SALT_BYTES = 16


def hash_password(
    password: str,
    pepper: str,
    iterations: int = PBKDF2_DEFAULT_ITERATIONS,
    salt: str = "",
) -> str:
    if not PBKDF2_MIN_ITERATIONS <= iterations <= PBKDF2_MAX_ITERATIONS:
        raise ValueError(
            f"PBKDF2 iterations must be between "
            f"{PBKDF2_MIN_ITERATIONS} and {PBKDF2_MAX_ITERATIONS}"
        )
    if not salt:
        salt = secrets.token_hex(PBKDF2_SALT_BYTES)
    if "$" in salt:
        raise ValueError("PBKDF2 salt must not contain '$'")

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        f"{password}{pepper}".encode(),
        salt.encode(),
        iterations,
    )
    return f"{PBKDF2_SCHEME}${iterations}${salt}${digest.hex()}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate password hash for specs/security/users.yaml")
    parser.add_argument("--password", required=True)
    parser.add_argument("--pepper", required=True)
    parser.add_argument(
        "--algo",
        choices=[PBKDF2_SCHEME],
        default=PBKDF2_SCHEME,
        help="Password hashing algorithm (legacy fast hashes are not supported)",
    )
    parser.add_argument("--iterations", type=int, default=PBKDF2_DEFAULT_ITERATIONS)
    parser.add_argument("--salt", default="")
    args = parser.parse_args()

    try:
        password_hash = hash_password(
            password=args.password,
            pepper=args.pepper,
            iterations=args.iterations,
            salt=args.salt,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(password_hash)


if __name__ == "__main__":
    main()
