# Convert Minecraft Bedrock local player to network player

This is a workaround for [Mojang bug
BDS-5121](https://bugs.mojang.com/browse/BDS-5121), affecting people
attempting to transfer a world from being hosted on a device (e.g. a phone)
to a Bedrock Dedicated Server.  Previously the only known workaround was to
place everything from your inventory in a box before transferring the world
to a BDS, but this wasn't very satisfactory: among other things, it didn't
account for pets.  The code in this repository eliminates the need for that
workaround by making the appropriate changes directly in the world database.

The hard bit is figuring out how the original local player should be
represented in the database.  There may well be a better way to do this, but
my approach is to get the player in question to connect to a scratch copy of
the world, compare the database from before and after that connection to see
how Minecraft and BDS themselves decided to represent them, and then rename
everything related to the original local player.

Disclaimers: I am not affiliated with Mojang or Microsoft in any way, nor am
I a Minecraft expert: in fact, I don't even play Minecraft myself, just
somehow ended up fixing this for my family.  Writing this was a last resort
after failing to find any other acceptable way to fix the problem at hand.
As such, I may very well have got various technical details wrong.  You
**must** ensure that you have a backup of the world before using this
program and that you know how to restore it.  While I've tried to include
somewhat reasonable error handling, I only had a single sample world to work
with when writing this, so there may be problems I couldn't foresee.

You will need Python >= 3.6.

## Usage

1. Grab and build these [Python bedrock
   bindings](https://github.com/BluCodeGH/bedrock) and (if necessary)
   [leveldb-mcpe](https://github.com/Mojang/leveldb-mcpe).  Add the
   `bedrock` directory to your `PYTHONPATH` for the remaining steps.
2. Take a clean copy of the world from the original device.  (I used `adb
   backup` and [Android Backup
   Extractor](https://github.com/nelenkov/android-backup-extractor), but of
   course this depends on your original device.
3. Upload the world to a BDS instance (renaming its directory as usual - at
   a minimum it needs to not end with the `=` character to avoid confusing
   the BDS `server.properties` parser, but it's probably least confusing to
   rename it to match `levelname.txt`), configure `server.properties` to use
   it, and start the server.
4. Get the original local player to connect to the world.
5. Stop the server and copy the world back out.  Make sure to put it in a
   different path from the clean copy you took in step 2, because you'll
   need to compare them.
6. Run `compare-worlds.py <path to old world> <path to new world>`.  This
   should find a single new player and print various UUIDs associated with
   them.
7. Take another copy of the original world from step 2, and run
   `convert-local-player.py <path to copied world> <MSA ID> <self-signed ID>
   <player server ID>`, using the UUIDs printed in step 6.
8. Upload this modified copy to the BDS instance, overwriting the one you
   uploaded before, and restart the server.
9. The original local player should now be able to connect and see their
   inventory.

Once this modification has been made, the world will no longer be suitable
for use on the original device.  (My guess is that the original local player
will end up with no inventory, similar to the issue I was trying to solve
but in reverse.)  It should be possible to reverse the process by renaming
the appropriate database row back to `~local-player`, but I haven't tested
this.  PRs welcome if anyone else needs this.
