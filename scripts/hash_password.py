from __future__ import annotations

import argparse
import binascii
import hashlib
import hmac
import re
import secrets

SALT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def hash_password(password: str, pepper: str) -> str:
    return hashlib.sha256(f"{password}{pepper}".encode()).hexdigest()


def hash_password_pbkdf2(
    password: str,
    pepper: str,
    iterations: int = 390000,
    salt: str = "",
) -> str:
    if iterations < 1:
        raise ValueError("iterations must be >= 1")

    if not salt:
        salt = secrets.token_hex(8)
    _validate_salt(salt)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        f"{password}{pepper}".encode(),
        salt.encode(),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${binascii.hexlify(digest).decode()}"


def _validate_salt(salt: str) -> None:
    text = str(salt).strip()
    if not text:
        raise ValueError("salt must not be blank when provided")
    if "$" in text:
        raise ValueError("salt must not contain '$'")
    if not SALT_PATTERN.fullmatch(text):
        raise ValueError("salt must use only letters, numbers, '.', '_' or '-'")


def verify_password(password: str, pepper: str, stored_hash: str) -> bool:
    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations_str, salt, expected_hex = stored_hash.split("$", maxsplit=3)
            iterations = int(iterations_str)
            _validate_salt(salt)
            if iterations < 1:
                return False
            generated = hash_password_pbkdf2(
                password=password,
                pepper=pepper,
                iterations=iterations,
                salt=salt,
            )
            actual_hex = generated.rsplit("$", maxsplit=1)[-1]
            return hmac.compare_digest(expected_hex, actual_hex)
        except Exception:
            return False

    return hmac.compare_digest(hash_password(password, pepper), stored_hash)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate password hash for specs/security/users.yaml")
    parser.add_argument("--password", required=True)
    parser.add_argument("--pepper", required=True)
    parser.add_argument(
        "--algo",
        choices=["sha256", "pbkdf2_sha256"],
        default="pbkdf2_sha256",
        help="Hash algorithm format",
    )
    parser.add_argument("--iterations", type=int, default=390000)
    parser.add_argument("--salt", default="")
    parser.add_argument(
        "--verify-hash",
        default="",
        help="Validate --password/--pepper against an existing hash string",
    )
    args = parser.parse_args()

    if args.verify_hash:
        verified = verify_password(args.password, args.pepper, args.verify_hash.strip())
        if verified:
            print("VERIFIED")
            return
        print("NOT_VERIFIED")
        raise SystemExit(1)

    if args.algo == "sha256":
        print(hash_password(args.password, args.pepper))
        return

    if args.iterations < 1:
        parser.error("--iterations must be >= 1")
    if args.salt:
        try:
            _validate_salt(args.salt)
        except ValueError as exc:
            parser.error(str(exc))

    print(
        hash_password_pbkdf2(
            password=args.password,
            pepper=args.pepper,
            iterations=args.iterations,
            salt=args.salt,
        )
    )


if __name__ == "__main__":
    main()
