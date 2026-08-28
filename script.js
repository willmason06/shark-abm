const canvas = document.getElementById("simulation");
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


// ==========================================
// IMAGES
// ==========================================

const fishImage = new Image();
fishImage.src = "fish.png";


const sharkImage = new Image();
sharkImage.src = "shark.png";


// ==========================================
// SIMULATION DATA
// ==========================================

let simulation = [];

let currentFrame = 0;


// ==========================================
// LOAD JSON
// ==========================================

async function loadSimulation() {

    const response = await fetch("simulation.json");

    simulation = await response.json();

    console.log("Simulation loaded");
    console.log("Frames:", simulation.length);

    requestAnimationFrame(animate);

}


// ==========================================
// DRAW BACKGROUND
// ==========================================

function drawBackground() {

    ctx.fillStyle = "#001d2e";

    ctx.fillRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

}


// ==========================================
// CONVERT SIMULATION POSITION
// TO CANVAS POSITION
// ==========================================

function scaleX(x) {

    return (x / 100) * canvas.width;

}


function scaleY(y) {

    // Flip Y because canvas Y increases downward

    return canvas.height - (
        (y / 100) * canvas.height
    );

}


// ==========================================
// DRAW FISH
// ==========================================

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


// ==========================================
// DRAW SHARK
// ==========================================

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


// ==========================================
// DRAW ONE FRAME
// ==========================================

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
// ANIMATION LOOP
// ==========================================

let lastTime = 0;

const frameDuration = 30;


// 30 milliseconds = ~33 simulation frames/sec


function animate(timestamp) {

    if (simulation.length === 0) {

        return;

    }


    if (timestamp - lastTime >= frameDuration) {

        drawFrame(
            simulation[currentFrame]
        );


        currentFrame += 1;


        // Loop back to beginning

        if (currentFrame >= simulation.length) {

            currentFrame = 0;

        }


        lastTime = timestamp;

    }


    requestAnimationFrame(animate);

}


// ==========================================
// START
// ==========================================

loadSimulation();