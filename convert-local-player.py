#! /usr/bin/python3

# Copyright (C) 2021 Colin Watson <cjwatson@chiark.greenend.org.uk>.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Convert a Minecraft world's "local player" to a network player.

When a world is hosted on a device such as a phone, it records the hosting
player's identity internally as "~local_player" rather than as their network
player ID.  As a result, if you copy that world to a Bedrock Dedicated
Server instance, the local player's inventory and other properties will
appear to vanish (https://bugs.mojang.com/browse/BDS-5121).

To work around this, use compare-worlds.py to find the various UUIDs
associated with the player in question, and then use this program to adjust
the world to use those.  You should run this against the unmodified original
version of the world, from before anyone connected to it via BDS.

You MUST ensure that you have a backup of the world before using this
program.

The world should not be used for locally-hosted play after using this
program; if you try, it will most likely have the opposite problem, in that
the local player will have lost their inventory.
"""

import argparse
import os.path

from bedrock import (
    leveldb as ldb,
    nbt,
)


parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("world", help="world path")
parser.add_argument("msa_id", help="MSA ID")
parser.add_argument("self_signed_id", help="Self-signed ID")
parser.add_argument("player_server_id", help="Player server ID")
args = parser.parse_args()

db = ldb.open(os.path.join(args.world, "db"))
ldb.put(
    db,
    f"player_server_{args.player_server_id}".encode(),
    ldb.get(db, b"~local_player"),
)
player = nbt.encode(
    nbt.TAG_Compound(
        "",
        [
            nbt.TAG_String("MsaId", args.msa_id),
            nbt.TAG_String("SelfSignedId", args.self_signed_id),
            nbt.TAG_String(
                "ServerId", f"player_server_{args.player_server_id}".encode()
            ),
        ],
    )
)
ldb.put(db, f"player_{args.msa_id}".encode(), player)
ldb.put(db, f"player_{args.self_signed_id}".encode(), player)
ldb.delete(db, b"~local_player")
ldb.close(db)
