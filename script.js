const canvas = document.getElementById("wheelCanvas");
const resultCanvas = document.getElementById("resultCanvas");
const ctx = canvas.getContext("2d");
const resultCtx = resultCanvas.getContext("2d");
const spinBtn = document.getElementById("spinBtn");

const wheelImg = new Image();
wheelImg.src = "Wheel.png";

const sliceLabels = [
  "Experimental Learning",
  "Programming Education",
  "Technology-Enhanced Learning",
  "AI in Education",
  "Educational Data Science",
  "Methodology & Meta-Research",
  "[empty]",
  "Societal Impact",
  "Experimental Learning"
];

let angle = 0;
let spinning = false;
let speed = 0;
let deceleration = 0.002;
let totalRotation = 0;

wheelImg.onload = () => {
  canvas.width = wheelImg.width;
  canvas.height = wheelImg.height;
  drawWheel();
};

function drawWheel() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate(angle);
  ctx.drawImage(wheelImg, -wheelImg.width / 2, -wheelImg.height / 2);
  ctx.restore();
}

function showResult(sliceIndex) {
  resultCtx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
  resultCtx.font = "16px Arial";
  resultCtx.fillStyle = "#333";
  resultCtx.textAlign = "center";

  const text = `List of topics to: ${sliceLabels[sliceIndex]}`;
  const maxWidth = resultCanvas.width - 20;
  const lineHeight = 24;
  const x = resultCanvas.width / 2;
  let y = resultCanvas.height / 2 - lineHeight / 2;

  // Word-wrapping logic
  const words = text.split(" ");
  let line = "";

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const metrics = resultCtx.measureText(testLine);
    const testWidth = metrics.width;

    if (testWidth > maxWidth && n > 0) {
      resultCtx.fillText(line.trim(), x, y);
      line = words[n] + " ";
      y += lineHeight;
    } else {
      line = testLine;
    }
  }
  resultCtx.fillText(line.trim(), x, y); // Draw the last line
}

function animate() {
  if (spinning) {
    angle += speed;
    totalRotation += speed;
    speed = Math.max(speed - deceleration, 0);

    if (speed === 0) {
      spinning = false;
	const deg = (angle * 180 / Math.PI) % 360;
	// Adjust by 90 degrees to align the RIGHT as the pointer (instead of top)
	const adjustedDeg = (deg + 270) % 360;
	const sliceIndex = Math.floor(((360 - adjustedDeg) % 360) / 45);
      showResult(sliceIndex);
    }
  }

  drawWheel();
  requestAnimationFrame(animate);
}

spinBtn.addEventListener("click", () => {
  if (!spinning) {
    speed = Math.random() * 0.2 + 0.3;
    totalRotation = 0;
    spinning = true;
    resultCtx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
  }
});

animate();
