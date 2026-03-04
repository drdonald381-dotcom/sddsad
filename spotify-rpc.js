const RPC = require("discord-rpc");
const SpotifyWebApi = require("spotify-web-api-node");

const discordClientId = "1434350607644364881";

const spotify = new SpotifyWebApi({
  clientId: "cf0abd65f262491ca7745daa37eb91fd",
  clientSecret: "aed9f190717e4b158b7ba5b0efd0494e",
  redirectUri: "http://127.0.0.1:8888/callback"
});

spotify.setRefreshToken("AQBbi0G8UfurRrYfhMLlfuugcLA-PlQjy6t-kps2Nh13_U0rh2IQdTnemKjNsxvHXCkFmmRzssKb3q4BA0qZaxGzvZJ6v44u1ePWzqE1CJOV9KqXrhkEI3SxVYV7Gy6mGPk");

const rpc = new RPC.Client({ transport: "ipc" });

async function update() {
  try {
    const refresh = await spotify.refreshAccessToken();
    spotify.setAccessToken(refresh.body.access_token);

    const current = await spotify.getMyCurrentPlayingTrack();

    if (current.body && current.body.item) {
      const track = current.body.item.name;
      const artist = current.body.item.artists[0].name;

      rpc.setActivity({
        details: track,
        state: artist,
        largeImageKey: "spotify_logo"
      });
    }
  } catch (e) {
    console.log(e);
  }
}

rpc.on("ready", () => {
  console.log("Discord RPC ready");
  setInterval(update, 5000);
});

rpc.login({ clientId: discordClientId });