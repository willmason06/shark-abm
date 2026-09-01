const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");


// ==========================================
// CANVAS SIZE
// ==========================================

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;


window.addEventListener("resize", () => {

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

});


const fishImage = new Image();
fishImage.src = "fish.png";

const sharkImage = new Image();
sharkImage.src = "shark.png";


let mouseX = 0;
let mouseY = 0;

canvas.addEventListener("mousemove", function(event) {
    const rect = canvas.getBoundingClientRect();

    // convert to model space (0..100), flipping Y since the model's Y
    // increases upward but canvas/mouse Y increases downward
    mouseX = ((event.clientX - rect.left) / rect.width) * 100;
    mouseY = 100 - ((event.clientY - rect.top) / rect.height) * 100;
});


// ==========================================
// LIVE STATE FROM THE SERVER
// ==========================================

// currentFrame is what gets drawn every render tick. It's updated
// whenever a fetch to the server resolves, independent of the render
// loop's own timing, so a slow network response never blocks drawing.

let currentFrame = { fish: [], sharks: [] };


function toFrame(fish_positions, fish_velocities, shark_positions, shark_velocities) {

    const fish = fish_positions.map((pos, i) => {
        const vel = fish_velocities[i];

        return {
            x: pos[0],
            y: pos[1],
            angle: Math.atan2(vel[1], vel[0])
        };
    });

    const sharks = shark_positions.map((pos, i) => {
        const vel = shark_velocities[i];

        return {
            x: pos[0],
            y: pos[1],
            angle: Math.atan2(vel[1], vel[0])
        };
    });

    return { fish, sharks };

}


async function updateShark() {

    const response = await fetch("http://127.0.0.1:5000/abm_fish_server", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            mouseX: mouseX,
            mouseY: mouseY
        })
    });

    const data = await response.json();

    currentFrame = toFrame(
        data.fish_positions,
        data.fish_velocities,
        data.shark_positions,
        data.shark_velocities
    );

}


function drawBackground() {

    ctx.fillStyle = "#001d2e";

    ctx.fillRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

}


function scaleX(x) {

    return (x / 100) * canvas.width;

}


function scaleY(y) {

    // Flip Y because canvas Y increases downward

    return canvas.height - (
        (y / 100) * canvas.height
    );

}

function drawFish(fish) {

    const x = scaleX(fish.x);

    const y = scaleY(fish.y);


    ctx.save();


    // Move drawing origin to fish

    ctx.translate(x, y);


    // Rotate fish

    ctx.rotate(-fish.angle);


    // Draw fish centred on position

    ctx.drawImage(

        fishImage,

        -15,
        -15,

        30,
        30

    );


    ctx.restore();

}


function drawShark(shark) {

    const x = scaleX(shark.x);

    const y = scaleY(shark.y);


    ctx.save();


    // Move drawing origin to shark

    ctx.translate(x, y);


    // Rotate shark

    ctx.rotate(-shark.angle);


    // Draw shark centred on position

    ctx.drawImage(

        sharkImage,

        -35,
        -35,

        70,
        70

    );


    ctx.restore();

}


function drawFrame(frame) {

    drawBackground();


    // -------------------------
    // DRAW FISH
    // -------------------------

    for (const fish of frame.fish) {

        drawFish(fish);

    }


    // -------------------------
    // DRAW SHARKS
    // -------------------------

    for (const shark of frame.sharks) {

        drawShark(shark);

    }

}


// ==========================================
// RENDER LOOP  (draws whatever the latest fetched frame is)
// ==========================================

function animate(timestamp) {

    drawFrame(currentFrame);

    requestAnimationFrame(animate);

}


// ==========================================
// FETCH LOOP  (polls the server on its own cadence)
// ==========================================

const fetchInterval = 30; // ms between requests to the server

async function fetchLoop() {

    while (true) {

        try {

            await updateShark();

        } catch (error) {

            console.error("Failed to fetch simulation update:", error);

        }

        await new Promise(resolve => setTimeout(resolve, fetchInterval));

    }

}


requestAnimationFrame(animate);
fetchLoop();