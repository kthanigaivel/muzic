const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "/default";
}

function getToken() {
    return localStorage.getItem("token");
}

function getAuthHeaders() {
    const token = getToken();
    if (!token) {
        logout();
        return null;
    }
    return {
        "Authorization": `Bearer ${token}`
    };
}

let songs = [];
let filteredSongs = [];
let favorites = new Set();
let currentUser = null;

let currentSong = null;
let currentIndex = -1;
let player = null;
let playHistorySent = false;
let lastPlayedHistory = null;

document.addEventListener("DOMContentLoaded", async () => {

    player = document.getElementById("player");

    initializePlayer();

    updateGreeting();

    await loadCurrentUser();
    await loadFavoriteIds();
    await loadSongs();

});

async function loadCurrentUser() {

    try {

        const authHeaders = getAuthHeaders();
        if (!authHeaders) return;

        const response = await fetch("/auth/me", {
            headers: {
                ...authHeaders,
                "Accept": "application/json"
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            throw new Error();
        }

        const user = await response.json();

        document.getElementById("profile-name").textContent =
            user.username;

        document.getElementById("profile-image").src =
            `https://ui-avatars.com/api/?background=1DB954&color=fff&name=${encodeURIComponent(user.username)}`;

        currentUser = user;
        updateGreeting();

    }

    catch (err) {

        console.error(err);

        logout();

    }

}

async function loadFavoriteIds() {

    try {

        const authHeaders = getAuthHeaders();
        if (!authHeaders) return;

        const response = await fetch("/favorite", {
            headers: {
                ...authHeaders,
                "Accept": "application/json"
            }
        });

        if (response.status === 401) {

            logout();
            return;

        }

        if (!response.ok) {

            throw new Error();

        }

        const data = await response.json();

        favorites = new Set(
            data.map(song => song.youtube_id)
        );

    }

    catch (err) {

        console.error(err);

    }

}

function toggleProfile() {

    document
        .getElementById("profile-menu")
        .classList
        .toggle("show");

}

window.addEventListener("click", function (e) {

    const profile =
        document.querySelector(".profile");

    const menu =
        document.getElementById("profile-menu");

    if (!profile.contains(e.target)) {

        menu.classList.remove("show");

    }

});

function logout() {

    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user");

    window.location.href = "/default";

}

async function loadSongs() {

    try {

        const authHeaders = getAuthHeaders();
        if (!authHeaders) return;

        const response = await fetch("/songs/", {
            headers: {
                ...authHeaders,
                "Accept": "application/json"
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (!response.ok) {
            throw new Error("Unable to load songs");
        }

        songs = await response.json();

        filteredSongs = [...songs];

        renderSongs();

    }

    catch (err) {

        console.error(err);

    }

}

function showFavorites() {

    filteredSongs = songs.filter(song =>
        favorites.has(song.youtube_id)
    );

    renderSongs();

}

function showShuffle() {

    const shuffledSongs = [...songs];

    for (let i = shuffledSongs.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffledSongs[i], shuffledSongs[j]] = [shuffledSongs[j], shuffledSongs[i]];
    }

    filteredSongs = shuffledSongs;

    renderSongs();

}

function filterSongs() {

    const q = document
        .getElementById("search")
        .value
        .toLowerCase();

    filteredSongs = songs.filter(song =>

        song.filename.toLowerCase().includes(q)

        ||

        song.youtube_id.toLowerCase().includes(q)

    );

    renderSongs();

}

function renderSongs() {

    const container = document.getElementById("songs");

    if (!container) return;

    container.innerHTML = filteredSongs.map((song, index) => `

<div class="song-card" onclick="playSong(${index})">

    <div class="cover">

        <img src="/media/${song.youtube_id}.jpg">

    </div>

    <div style="flex:1">

        <div class="song-title">

            ${song.filename.split("|").slice(1).join(" ")}

        </div>

        <div class="song-artist">

            ${song.youtube_id}

        </div>

        <div
            class="favorite"
            onclick="event.stopPropagation();toggleFavorite('${song.youtube_id}')">

            ${favorites.has(song.youtube_id) ? "❤️" : "🤍"}

        </div>

    </div>

</div>

`).join("");

}

async function toggleFavorite(youtube_id) {

    try {

        const method =
            favorites.has(youtube_id)
                ? "DELETE"
                : "POST";

        const authHeaders = getAuthHeaders();
        if (!authHeaders) return;

        const response = await fetch(`/favorite/${youtube_id}`, {
            method,
            headers: authHeaders
        });

        if (!response.ok) {

            throw new Error();

        }

        if (method === "POST") {

            favorites.add(youtube_id);

        } else {

            favorites.delete(youtube_id);

        }
        updatePlayerFavorite();
        renderSongs();


    }

    catch (err) {

        console.error(err);

    }

}

function updatePlayerFavorite() {

    const btn =
        document.getElementById("playerFavorite");

    if (!currentSong) {

        btn.textContent = "🤍";
        return;

    }

    btn.textContent =
        favorites.has(currentSong.youtube_id)
            ? "❤️"
            : "🤍";

}


function initializePlayer() {

    player.addEventListener("play", () => {
        document.getElementById("playBtn").innerHTML = "⏸";
    });

    player.addEventListener("pause", () => {
        document.getElementById("playBtn").innerHTML = "▶";
    });

    player.addEventListener("ended", () => {
        nextSong();
    });

    player.addEventListener("volumechange", () => {

        localStorage.setItem(
            "velora_volume",
            player.volume
        );

        localStorage.setItem(
            "velora_muted",
            player.muted
        );

    });

    const savedVolume =
        localStorage.getItem("velora_volume");

    if (savedVolume !== null) {

        player.volume = parseFloat(savedVolume);

    } else {

        player.volume = 0.7;

    }

    const muted =
        localStorage.getItem("velora_muted");

    if (muted !== null) {

        player.muted = muted === "true";

    }



    player.addEventListener("playing", async () => {

        if (!currentSong) return;

        if (lastPlayedHistory === currentSong.youtube_id)
            return;

        lastPlayedHistory = currentSong.youtube_id;

        try {

            await fetch(
                "/songs/play?youtube_id=" + currentSong.youtube_id,
                {
                    method: "POST",
                    headers: {
                        "Authorization": "Bearer " + token
                    }
                }
            );

        } catch (err) {

            console.error(err);

        }

    });

}
function playSong(songOrIndex) {

    if (typeof songOrIndex === "number") {

        if (songOrIndex < 0 || songOrIndex >= filteredSongs.length)
            return;

        currentIndex = songOrIndex;
        currentSong = filteredSongs[songOrIndex];

    } else {

        currentSong = songOrIndex;
        currentIndex = songs.findIndex(
            s => s.youtube_id === currentSong.youtube_id
        );

    }

    lastPlayedHistory = false;
    updatePlayerFavorite();

    player.src = `/media/${currentSong.youtube_id}.mp3`;

    document.getElementById("current-cover").src =
        `/media/${currentSong.youtube_id}.jpg`;

    document.getElementById("song-name").textContent =
        currentSong.filename.split("|").slice(1).join(" ");

    document.getElementById("artist-name").textContent =
        currentSong.youtube_id;

    player.play();
}


function togglePlay() {

    if (!currentSong || !player.src) {
        alert("Please select a song first.");
        return;
    }

    if (player.paused) {
        player.play();
    } else {
        player.pause();
    }

}

function nextSong() {

    if (filteredSongs.length === 0)
        return;

    currentIndex++;

    if (currentIndex >= filteredSongs.length) {

        currentIndex = 0;

    }

    playSong(currentIndex);

}


function prevSong() {

    if (filteredSongs.length === 0)
        return;

    currentIndex--;

    if (currentIndex < 0) {

        currentIndex =
            filteredSongs.length - 1;

    }

    playSong(currentIndex);

}


async function randomSong() {

    const activeList = filteredSongs.length ? filteredSongs : songs;

    if (activeList.length === 0) {
        console.error("No songs available for random selection");
        return;
    }

    const randomIndex = Math.floor(Math.random() * activeList.length);

    playSong(randomIndex);
}


async function toggleCurrentFavorite() {

    if (!currentSong)
        return;

    await toggleFavorite(currentSong.youtube_id);

    updatePlayerFavorite();

}

function updateGreeting() {

    const hour = new Date().getHours();

    let greeting = "Hello";

    if (hour >= 5 && hour < 12) {
        greeting = "Good Morning";
    } else if (hour >= 12 && hour < 17) {
        greeting = "Good Afternoon";
    } else if (hour >= 17 && hour < 21) {
        greeting = "Good Evening";
    } else {
        greeting = "Good Night";
    }

    const capitalize = value => value
        .split(" ")
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(" ");

    const name = currentUser?.username ? `, ${capitalize(currentUser.username)}` : "";
    document.getElementById("greeting").textContent =
        `${greeting}${name}`;

}









document.addEventListener("keydown", function (e) {

    // Ignore shortcuts while typing
    if (
        e.target.tagName === "INPUT" ||
        e.target.tagName === "TEXTAREA"
    ) {
        return;
    }

    switch (e.code) {

        case "Space":

            e.preventDefault();

            togglePlay();

            break;

        case "ArrowRight":

            nextSong();

            break;

        case "ArrowLeft":

            prevSong();

            break;

        case "KeyF":

            document
                .getElementById("search")
                .focus();

            break;

    }

});

