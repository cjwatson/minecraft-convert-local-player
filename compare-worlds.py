#!/usr/bin/env python3

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

"""Compare two Minecraft world databases, looking for new players.

This can be used to work out the UUIDs associated with a player for network
play.  First, transfer a clean copy of the world to a Bedrock Dedicated
Server instance, and get the player in question to connect to it.  Then stop
the server and copy the world back out, making sure to copy it to a
different path so that you have both old and new versions.  Finally, run
this script with the paths to the old and new versions of the world; it
should print the UUIDs associated with any new players who have appeared.
"""

import argparse
import os.path

from bedrock import (
    leveldb as ldb,
    nbt,
)


def get_players(db):
    return {
        key: value
        for key, value in ldb.iterate(db)
        if key.startswith(b"player_") and not key.startswith(b"player_server_")
    }


parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("old_world", help="old world path")
parser.add_argument("new_world", help="new world path")
args = parser.parse_args()

old_db = ldb.open(os.path.join(args.old_world, "db"))
old_players = get_players(old_db)
ldb.close(old_db)

new_db = ldb.open(os.path.join(args.new_world, "db"))
new_players = get_players(new_db)
ldb.close(new_db)

players_by_msa = {}
player_server_len = len("player_server_")
for player_key in sorted(set(new_players) - set(old_players)):
    player = nbt.decode(nbt.DataReader(new_players[player_key]))
    if not isinstance(player, nbt.TAG_Compound):
        raise Exception(f"Can't understand player of type {type(player)}")
    player_dict = {tag.name: tag.payload for tag in player.payload}
    for required_tag in ("MsaId", "SelfSignedId", "ServerId"):
        if required_tag not in player_dict:
            raise Exception(f"No {required_tag} tag in {player}")
    if not player_dict["ServerId"].startswith("player_server_"):
        raise Exception(
            f"Player server ID does not start with player_server_: {player}"
        )
    players_by_msa[player_dict["MsaId"]] = (
        player_dict["SelfSignedId"],
        player_dict["ServerId"][player_server_len:],
    )

for msa_id, (self_signed_id, player_server_id) in sorted(
    players_by_msa.items()
):
    print("New player:")
    print(f"  MSA ID: {msa_id}")
    print(f"  Self-signed ID: {self_signed_id}")
    print(f"  Player server ID: {player_server_id}")
