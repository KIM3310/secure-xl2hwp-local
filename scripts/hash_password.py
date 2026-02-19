from __future__ import annotations

import argparse
import binascii
import hashlib
import secrets


def hash_password(password: str, pepper: str) -> str:
    return hashlib.sha256(f"{password}{pepper}".encode()).hexdigest()


def hash_password_pbkdf2(
    password: str,
    pepper: str,
    iterations: int = 390000,
    salt: str = "",
) -> str:
    if not salt:
        salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        f"{password}{pepper}".encode(),
        salt.encode(),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${binascii.hexlify(digest).decode()}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate password hash for specs/security/users.yaml")
    parser.add_argument("--password", required=True)
    parser.add_argument("--pepper", default="change-this-pepper")
    parser.add_argument(
        "--algo",
        choices=["sha256", "pbkdf2_sha256"],
        default="sha256",
        help="Hash algorithm format",
    )
    parser.add_argument("--iterations", type=int, default=390000)
    parser.add_argument("--salt", default="")
    args = parser.parse_args()

    if args.algo == "sha256":
        print(hash_password(args.password, args.pepper))
        return

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
