"""envault — A CLI tool for managing and encrypting environment variables across multiple projects and environments."""

__version__ = "0.1.0"
__author__ = "envault contributors"

from envault.crypto import encrypt, decrypt

__all__ = ["encrypt", "decrypt"]
