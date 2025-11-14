"""
TypeScript and Prisma parsers for SpecQL reverse engineering.
"""

from .prisma_parser import PrismaParser
from .typescript_parser import TypeScriptParser

__all__ = ["PrismaParser", "TypeScriptParser"]
