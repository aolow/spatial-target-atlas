"""DBCLS-aligned expression masks for the central anatomy illustration.

Coordinates below are authored in the DBCLS source SVG coordinate system
(600 x 1000). They are visualization masks, not diagnostic segmentations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class SourcePath:
    d: str


Shape: TypeAlias = SourcePath


REGIONS: dict[str, tuple[Shape, ...]] = {
    "brain": (
        SourcePath(
            "M245 48 C260 30 310 30 330 48 "
            "C344 62 340 102 322 120 "
            "C304 134 272 134 252 118 "
            "C236 101 232 66 245 48 Z"
        ),
    ),
    "lung": (
        SourcePath(
            "M218 225 C205 250 202 320 215 360 "
            "C224 386 249 393 270 368 "
            "C283 343 282 288 273 248 "
            "C265 222 237 211 218 225 Z"
        ),
        SourcePath(
            "M382 225 C395 250 398 320 385 360 "
            "C376 386 351 393 330 368 "
            "C317 343 318 288 327 248 "
            "C335 222 363 211 382 225 Z"
        ),
    ),
    "liver": (
        SourcePath(
            "M285 385 C320 365 385 365 415 388 "
            "C422 410 405 440 370 453 "
            "C340 461 305 448 282 425 "
            "C275 410 277 397 285 385 Z"
        ),
    ),
    "kidney": (
        SourcePath(
            "M246 448 C228 450 219 473 223 508 "
            "C226 538 242 554 258 542 "
            "C270 532 267 505 276 486 "
            "C272 464 262 450 246 448 Z"
        ),
        SourcePath(
            "M354 448 C372 450 381 473 377 508 "
            "C374 538 358 554 342 542 "
            "C330 532 333 505 324 486 "
            "C328 464 338 450 354 448 Z"
        ),
    ),
}
