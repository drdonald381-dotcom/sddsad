const SpotifyWebApi = require("spotify-web-api-node");
const http = require("http");
const url = require("url");

const spotify = new SpotifyWebApi({
  clientId: "cf0abd65f262491ca7745daa37eb91fd",
  clientSecret: "aed9f190717e4b158b7ba5b0efd0494e",
  redirectUri: "http://127.0.0.1:8888/callback"
});

const authUrl = spotify.createAuthorizeURL(
  ["user-read-currently-playing", "user-read-playback-state"],
  "state123"
);
console.log("Open this link in your browser:");
console.log(authUrl);

const server = http.createServer(async (req, res) => {
  const query = url.parse(req.url, true).query;
  if (query.code) {
    try {
      const data = await spotify.authorizationCodeGrant(query.code);
      console.log("Refresh token:");
      console.log(data.body.refresh_token);
      res.end("You can close this window");
      server.close();
    } catch (e) {
      console.log(e);
    }
  } else {
    res.end("No code found");
  }
});

server.listen(8888);