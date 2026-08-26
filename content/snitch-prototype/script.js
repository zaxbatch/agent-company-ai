// ===== GAME DATA =====
const SPACE_TYPES = {
    START: 'start',
    FINISH: 'finish',
    DECISION: 'decision',
    EVENT: 'event',
    POINT: 'point',
    TRUST: 'trust',
    PENALTY: 'penalty',
    BLANK: 'blank',
    SPECIAL: 'special'
};

const DECISION_SCENARIOS = [
    {
        title: '🧀 Cheese in the Stomach',
        description: 'You find a piece of cheese floating in the stomach acid. Do you grab it?',
        options: [
            { text: '🍽️ Grab it! (Gain 4 pts, -1 Trust)', points: 4, trust: -1 },
            { text: '🤝 Share it (+2 Trust, +2 pts)', points: 2, trust: 2 },
            { text: '⚠️ Leave it (It might be poisonous)', points: 0, trust: 1 }
        ]
    },
    {
        title: '🐀 Snitching in the Intestine',
        description: 'You see another rat stealing food. Do you snitch?',
        options: [
            { text: '🐀 Snitch! (Gain 5 pts, -2 Trust)', points: 5, trust: -2 },
            { text: '🤐 Keep quiet (Gain 2 Trust)', points: 0, trust: 2 },
            { text: '🍽️ Join them (Gain 3 pts, -1 Trust)', points: 3, trust: -1 }
        ]
    },
    {
        title: '💪 Bullying in the Bile Duct',
        description: 'A group of rats is picking on a smaller rat. Do you help?',
        options: [
            { text: '🦸 Save them! (+3 Trust, +3 pts)', points: 3, trust: 3 },
            { text: '🐀 Snitch on bullies (Gain 4 pts, -1 Trust)', points: 4, trust: -1 },
            { text: '👀 Walk away (Lose 1 Trust)', points: 0, trust: -1 }
        ]
    },
    {
        title: '💎 Treasure in the Colon',
        description: 'You find a golden piece of corn. Do you keep it or share it?',
        options: [
            { text: '❤️ Share it (+2 Trust, +2 pts)', points: 2, trust: 2 },
            { text: '💰 Keep it (Gain 5 pts, -2 Trust)', points: 5, trust: -2 },
            { text: '🤔 Split it (Gain 3 pts, +1 Trust)', points: 3, trust: 1 }
        ]
    }
];

const EVENT_SCENARIOS = [
    {
        title: '💨 Stomach Gas!',
        description: 'A massive gas bubble forms!',
        action: (player) => {
            const roll = rollDice();
            if (roll >= 4) {
                player.points += 2;
                return `Rolled ${roll}! You ride the bubble forward! 🏄`;
            } else {
                player.trust -= 1;
                return `Rolled ${roll}! You get covered in gas... Lose 1 Trust. 😷`;
            }
        }
    },
    {
        title: '🌊 Acid Wave!',
        description: 'A wave of stomach acid splashes through!',
        action: (player) => {
            const roll = rollDice();
            if (roll >= 3) {
                player.points += 3;
                return `Rolled ${roll}! You surf the acid wave and find 3 points! 🌊`;
            } else {
                player.position = Math.max(0, player.position - 2);
                return `Rolled ${roll}! You get pushed back 2 spaces! 😰`;
            }
        }
    },
    {
        title: '🧀 Cheese Rain!',
        description: 'Cheese falls from the snake\'s last meal!',
        action: (player) => {
            return 'Cheese for everyone! 🧀';
        }
    }
];

// ===== GAME STATE =====
let currentPlayerIndex = 0;
let players = [];
let boardSpaces = [];
let gameOver = false;
let awaitingDecision = false;
let isPooping = false;

// ===== DOM REFS =====
const boardContainer = document.getElementById('board-container');
const playersPanel = document.getElementById('players-panel');
const playersListEl = document.getElementById('players-list');
const currentPlayerEl = document.getElementById('current-player');
const diceResultEl = document.getElementById('dice-result');
const turnMessageEl = document.getElementById('turn-message');
const rollBtn = document.getElementById('roll-btn');
const newGameBtn = document.getElementById('new-game-btn');
const spaceDotsGroup = document.getElementById('space-dots');
const playerBulgesGroup = document.getElementById('player-bulges');

// Intro elements
const introOverlay = document.getElementById('intro-overlay');
const introAnimation = document.getElementById('intro-animation');
const introStatus = document.getElementById('intro-status');
const introStartBtn = document.getElementById('intro-start-btn');

// Poop elements
const poopOverlay = document.getElementById('poop-overlay');
const poopAnimation = document.getElementById('poop-animation');
const poopMessage = document.getElementById('poop-message');
const poopCloseBtn = document.getElementById('poop-close-btn');

// Modals
const decisionModal = document.getElementById('decision-modal');
const decisionTitle = document.getElementById('decision-title');
const decisionDescription = document.getElementById('decision-description');
const decisionOptions = document.getElementById('decision-options');

const eventModal = document.getElementById('event-modal');
const eventTitle = document.getElementById('event-title');
const eventDescription = document.getElementById('event-description');
const eventCloseBtn = document.getElementById('event-close-btn');

// ===== UTILITY FUNCTIONS =====
function rollDice() {
    return Math.floor(Math.random() * 6) + 1;
}

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pickRandom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function getPointOnPath(progress) {
    const path = document.getElementById('snake-path');
    if (!path) return { x: 50, y: 250 };
    const length = path.getTotalLength();
    const point = path.getPointAtLength(progress * length);
    return { x: point.x, y: point.y };
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ===== PLAYER COUNT PROMPT =====
function getPlayerCount() {
    let count = 4;
    while (true) {
        const input = prompt('How many players? (2-8):', '4');
        if (input === null) {
            // User clicked cancel, default to 4
            break;
        }
        const parsed = parseInt(input);
        if (!isNaN(parsed) && parsed >= 2 && parsed <= 8) {
            count = parsed;
            break;
        }
        alert('Please enter a number between 2 and 8.');
    }
    return count;
}

// ===== INTRO ANIMATION =====
async function playIntro(playerCount) {
    introOverlay.classList.remove('hidden');
    introStartBtn.disabled = true;
    introStartBtn.textContent = '🎬 Eating rats...';
    introStatus.textContent = `🐍 The snake is hungry for ${playerCount} rats...`;

    const ratEmojis = ['🐀', '🐭', '🐹'];
    introAnimation.innerHTML = `
        <div class="intro-scene">
            <div class="intro-snake">🐍</div>
            ${Array.from({length: playerCount}, (_, i) =>
                `<div class="intro-rat" id="intro-rat-${i}" style="left: ${10 + i * 11}%; bottom: ${30 + Math.random() * 40}px;">${ratEmojis[i % 3]}</div>`
            ).join('')}
        </div>
    `;

    const snakeEl = introAnimation.querySelector('.intro-snake');
    const ratEls = introAnimation.querySelectorAll('.intro-rat');

    for (let i = 0; i < ratEls.length; i++) {
        await sleep(300);
        ratEls[i].classList.add('visible');
        introStatus.textContent = `🐀 Rat ${i + 1} arrived!`;
    }

    await sleep(500);
    introStatus.textContent = '😋 The snake is ready to eat!';

    for (let i = 0; i < ratEls.length; i++) {
        snakeEl.classList.add('eating');
        introStatus.textContent = `😮 Eating rat ${i + 1}...`;

        await sleep(400);
        ratEls[i].classList.add('eaten');
        ratEls[i].textContent = '💨';

        await sleep(400);
        snakeEl.classList.remove('eating');

        const burp = document.createElement('div');
        burp.textContent = '💨';
        burp.style.cssText = `
            position: absolute;
            font-size: 1.5rem;
            left: 50%;
            top: 20px;
            animation: poopEject 0.8s ease-out forwards;
        `;
        introAnimation.querySelector('.intro-scene').appendChild(burp);

        await sleep(300);
        ratEls.forEach((el, idx) => {
            if (idx > i) {
                el.textContent = ratEmojis[idx % 3];
            }
        });

        introStatus.textContent = `😋 ${i + 1}/${ratEls.length} rats eaten!`;
    }

    await sleep(500);
    introStatus.textContent = '🐍 All rats are inside the snake!';
    snakeEl.textContent = '🐍💤';

    await sleep(300);
    introStatus.textContent = '🎮 Ready to play!';
    introStartBtn.disabled = false;
    introStartBtn.textContent = '🎮 Start Game!';
}

// ===== POOP ANIMATION =====
async function playPoopAnimation(winner) {
    poopOverlay.classList.remove('hidden');
    poopAnimation.innerHTML = '';
    poopMessage.innerHTML = '';

    const scene = document.createElement('div');
    scene.className = 'poop-scene';
    scene.innerHTML = `
        <div class="poop-snake">🐍</div>
        <div class="poop-rat" id="poop-rat" style="left: 50%; bottom: 80px; transform: translateX(-50%);">${winner.emoji}</div>
    `;
    poopAnimation.appendChild(scene);

    poopMessage.innerHTML = `
        <div style="font-size: 1.5rem; color: #ffd93d; margin-bottom: 5px;">
            💩 ${winner.emoji} ${winner.name} got POOPED OUT! 💩
        </div>
        <div class="poop-stats">
            <span>💰 ${winner.points} Points</span>
            <span>🤝 ${winner.trust} Trust</span>
            <span>🏆 Winner!</span>
        </div>
    `;

    const ratEl = document.getElementById('poop-rat');
    const snakeEl = scene.querySelector('.poop-snake');

    await sleep(300);

    ratEl.style.transition = 'all 0.8s cubic-bezier(0.68, -0.55, 0.27, 1.55)';
    ratEl.style.bottom = '30px';
    ratEl.style.transform = 'translateX(-50%) scale(0.8)';

    await sleep(800);

    snakeEl.style.transition = 'transform 0.3s ease';
    snakeEl.style.transform = 'translateX(-50%) scale(0.9)';

    await sleep(300);
    snakeEl.style.transform = 'translateX(-50%) scale(1.1)';

    await sleep(300);
    snakeEl.style.transform = 'translateX(-50%) scale(1)';

    ratEl.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
    ratEl.style.bottom = '100px';
    ratEl.style.transform = 'translateX(100%) scale(1.3) rotate(20deg)';

    const poopEmojis = ['💩', '💨', '✨', '🌟', '💫', '🎉', '🎊'];
    const particlePositions = [
        { x: -60, y: -40 }, { x: -30, y: -60 }, { x: 0, y: -70 },
        { x: 30, y: -60 }, { x: 60, y: -40 }, { x: -45, y: -20 },
        { x: 45, y: -20 }, { x: -15, y: -80 }, { x: 15, y: -80 }
    ];

    particlePositions.forEach((pos, i) => {
        const particle = document.createElement('div');
        particle.className = 'poop-particle';
        particle.textContent = pickRandom(poopEmojis);
        particle.style.cssText = `
            left: 50%;
            bottom: 30px;
            --tx: ${pos.x}px;
            --ty: ${pos.y}px;
            animation-delay: ${i * 0.05}s;
        `;
        scene.appendChild(particle);
        setTimeout(() => {
            particle.classList.add('fly');
        }, 50);
    });

    const confettiEmojis = ['🎉', '🎊', '⭐', '🌟', '✨', '💫', '🎈', '🎁'];
    for (let i = 0; i < 12; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'poop-confetti';
        confetti.textContent = pickRandom(confettiEmojis);
        const leftPos = 10 + Math.random() * 80;
        confetti.style.cssText = `
            left: ${leftPos}%;
            bottom: 20px;
            animation-delay: ${0.5 + Math.random() * 1.5}s;
            font-size: ${1 + Math.random() * 0.8}rem;
        `;
        scene.appendChild(confetti);
    }

    const splashes = ['💩', '💨', '✨'];
    for (let i = 0; i < 5; i++) {
        const splash = document.createElement('div');
        splash.className = 'poop-splash';
        splash.textContent = pickRandom(splashes);
        splash.style.cssText = `
            left: ${40 + Math.random() * 20}%;
            bottom: ${20 + Math.random() * 30}px;
            animation-delay: ${i * 0.1}s;
        `;
        scene.appendChild(splash);
    }

    await sleep(500);

    ratEl.style.transition = 'all 0.4s ease';
    ratEl.style.opacity = '0';
    ratEl.style.transform = 'translateX(200%) scale(0) rotate(360deg)';

    await sleep(400);
    const finalPoop = document.createElement('div');
    finalPoop.textContent = '💩';
    finalPoop.style.cssText = `
        position: absolute;
        left: 50%;
        bottom: 20px;
        font-size: 4rem;
        transform: translateX(-50%) scale(0);
        transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        z-index: 20;
    `;
    scene.appendChild(finalPoop);

    await sleep(50);
    finalPoop.style.transform = 'translateX(-50%) scale(1.2)';
    await sleep(300);
    finalPoop.style.transform = 'translateX(-50%) scale(1)';

    const celebMsg = document.createElement('div');
    celebMsg.textContent = '🎉💩 POOPED! 💩🎉';
    celebMsg.style.cssText = `
        position: absolute;
        left: 50%;
        top: 10px;
        font-size: 1.5rem;
        font-weight: bold;
        color: #ffd93d;
        transform: translateX(-50%) scale(0);
        transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        z-index: 30;
        text-shadow: 0 0 20px rgba(255, 217, 61, 0.5);
    `;
    scene.appendChild(celebMsg);

    await sleep(100);
    celebMsg.style.transform = 'translateX(-50%) scale(1)';

    poopCloseBtn.disabled = false;
    poopCloseBtn.textContent = '🎮 Play Again';
}

// ===== BOARD GENERATION =====
function generateBoard() {
    const spaces = [];
    const numSpaces = 50;

    const typeDistribution = [
        SPACE_TYPES.BLANK, SPACE_TYPES.BLANK, SPACE_TYPES.BLANK,
        SPACE_TYPES.DECISION, SPACE_TYPES.DECISION,
        SPACE_TYPES.EVENT,
        SPACE_TYPES.POINT, SPACE_TYPES.POINT,
        SPACE_TYPES.TRUST,
        SPACE_TYPES.PENALTY,
        SPACE_TYPES.SPECIAL
    ];

    for (let i = 0; i < numSpaces; i++) {
        let type;
        let label = '';
        let icon = '';

        if (i === 0) {
            type = SPACE_TYPES.START;
            label = '👄 Enter';
            icon = '👄';
        } else if (i === numSpaces - 1) {
            type = SPACE_TYPES.FINISH;
            label = '💩 Exit';
            icon = '💩';
        } else {
            type = pickRandom(typeDistribution);
            const locations = ['Stomach', 'Intestine', 'Bile Duct', 'Colon', 'Rectum'];
            const location = pickRandom(locations);
            switch(type) {
                case SPACE_TYPES.DECISION:
                    icon = '❓';
                    label = `${location} Decision`;
                    break;
                case SPACE_TYPES.EVENT:
                    icon = '⭐';
                    label = `${location} Event`;
                    break;
                case SPACE_TYPES.POINT:
                    icon = '💰';
                    label = `${location} +2 pts`;
                    break;
                case SPACE_TYPES.TRUST:
                    icon = '🤝';
                    label = `${location} +1 Trust`;
                    break;
                case SPACE_TYPES.PENALTY:
                    icon = '⛓️';
                    label = `${location} Penalty!`;
                    break;
                case SPACE_TYPES.SPECIAL:
                    icon = '🎯';
                    label = `${location} Special`;
                    break;
                default:
                    icon = '•';
                    label = location;
            }
        }

        spaces.push({
            id: i,
            type: type,
            label: label,
            icon: icon,
            players: []
        });
    }

    return spaces;
}

// ===== PLAYER MANAGEMENT =====
function createPlayers(playerCount) {
    const colors = ['#e94560', '#f5a623', '#6c5ce7', '#00b894', '#fd79a8', '#0984e3', '#fdcb6e', '#00cec9'];
    const names = ['Squeaky', 'Whiskers', 'Cheese', 'Scamper', 'Nibbles', 'Rusty', 'Pip', 'Tails'];
    const emojis = ['🐀', '🐭', '🐹', '🐀', '🐭', '🐹', '🐀', '🐭'];

    const newPlayers = [];
    for (let i = 0; i < playerCount; i++) {
        newPlayers.push({
            id: i,
            name: names[i % names.length] + (i >= names.length ? ` ${Math.floor(i/names.length)+1}` : ''),
            color: colors[i % colors.length],
            emoji: emojis[i % emojis.length],
            position: 0,
            points: 0,
            trust: 3,
            skipped: false
        });
    }
    return newPlayers;
}

// ===== GAME INITIALIZATION =====
async function initGame(playerCount = 4) {
    await playIntro(playerCount);

    introOverlay.classList.add('hidden');
    boardContainer.style.display = 'block';
    playersPanel.style.display = 'block';

    gameOver = false;
    awaitingDecision = false;
    isPooping = false;
    currentPlayerIndex = 0;

    boardSpaces = generateBoard();
    players = createPlayers(playerCount);
    players.forEach(p => p.position = 0);

    renderSnakeBoard();
    updatePlayersList();
    updateGameInfo();

    rollBtn.disabled = false;
    turnMessageEl.textContent = `🐀 ${players[0].emoji} ${players[0].name}'s turn! Roll the dice! 🎲`;
    hideAllModals();
    poopOverlay.classList.add('hidden');
}

// ===== RENDER SNAKE BOARD =====
function renderSnakeBoard() {
    spaceDotsGroup.innerHTML = '';
    playerBulgesGroup.innerHTML = '';

    const numSpaces = boardSpaces.length;

    for (let i = 0; i < numSpaces; i++) {
        const progress = i / (numSpaces - 1);
        const point = getPointOnPath(progress);
        const space = boardSpaces[i];

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', point.x);
        circle.setAttribute('cy', point.y);
        circle.setAttribute('r', i === 0 || i === numSpaces - 1 ? 10 : 6);
        circle.setAttribute('class', `space-dot ${space.type}`);
        circle.setAttribute('data-index', i);

        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `Space ${i}: ${space.label}`;
        circle.appendChild(title);

        spaceDotsGroup.appendChild(circle);

        if (i === 0 || i === numSpaces - 1 || space.type === SPACE_TYPES.DECISION) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', point.x);
            text.setAttribute('y', point.y + 20);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', '8');
            text.setAttribute('fill', '#ccc');
            text.textContent = i === 0 ? '👄' : i === numSpaces - 1 ? '💩' : '❓';
            spaceDotsGroup.appendChild(text);
        }
    }

    renderPlayerBulges();
}

function renderPlayerBulges() {
    playerBulgesGroup.innerHTML = '';

    const numSpaces = boardSpaces.length;

    players.forEach((player) => {
        const progress = player.position / (numSpaces - 1);
        const point = getPointOnPath(progress);

        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', 'player-bulge');

        const bulge = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        bulge.setAttribute('cx', point.x);
        bulge.setAttribute('cy', point.y + 2);
        bulge.setAttribute('rx', 18);
        bulge.setAttribute('ry', 14);
        bulge.setAttribute('fill', player.color);
        bulge.setAttribute('opacity', '0.6');
        bulge.setAttribute('stroke', '#fff');
        bulge.setAttribute('stroke-width', '2');

        const emoji = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        emoji.setAttribute('x', point.x);
        emoji.setAttribute('y', point.y + 6);
        emoji.setAttribute('text-anchor', 'middle');
        emoji.setAttribute('font-size', '16');
        emoji.textContent = player.emoji;

        const nameLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        nameLabel.setAttribute('x', point.x);
        nameLabel.setAttribute('y', point.y - 18);
        nameLabel.setAttribute('text-anchor', 'middle');
        nameLabel.setAttribute('font-size', '9');
        nameLabel.setAttribute('fill', '#fff');
        nameLabel.setAttribute('font-weight', 'bold');
        nameLabel.textContent = player.name.substring(0, 8);

        group.appendChild(bulge);
        group.appendChild(emoji);
        group.appendChild(nameLabel);

        if (player.position === numSpaces - 1 && gameOver) {
            const poop = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            poop.setAttribute('x', point.x + 30);
            poop.setAttribute('y', point.y + 10);
            poop.setAttribute('text-anchor', 'middle');
            poop.setAttribute('font-size', '30');
            poop.setAttribute('class', 'poop-eject');
            poop.textContent = '💩';
            group.appendChild(poop);
        }

        playerBulgesGroup.appendChild(group);
    });
}

// ===== UPDATE FUNCTIONS =====
function updatePlayersList() {
    playersListEl.innerHTML = '';
    players.forEach((player, index) => {
        const card = document.createElement('div');
        card.className = `player-card ${index === currentPlayerIndex ? 'active' : ''}`;
        card.innerHTML = `
            <div class="player-name" style="color:${player.color}">
                ${player.emoji} ${player.name}
            </div>
            <div class="player-stats">
                <span>💰 ${player.points}</span>
                <span>🤝 ${player.trust}</span>
                <span>📍 ${player.position}</span>
            </div>
        `;
        playersListEl.appendChild(card);
    });
}

function updateGameInfo() {
    if (players.length === 0) return;
    const player = players[currentPlayerIndex];
    currentPlayerEl.textContent = `🎯 Current: ${player.emoji} ${player.name}`;
}

// ===== SHOW WINNER =====
async function showWinner(player) {
    boardContainer.style.display = 'none';
    playersPanel.style.display = 'none';
    await playPoopAnimation(player);
}

// ===== GAME LOGIC =====
function handleRoll() {
    if (gameOver || awaitingDecision || isPooping) return;

    const player = players[currentPlayerIndex];
    const roll = rollDice();
    diceResultEl.textContent = `🎲 ${roll}`;

    let newPosition = player.position + roll;

    if (newPosition >= boardSpaces.length - 1) {
        newPosition = boardSpaces.length - 1;
        gameOver = true;
        rollBtn.disabled = true;
        isPooping = true;

        player.position = newPosition;
        renderPlayerBulges();

        setTimeout(() => {
            showWinner(player);
            isPooping = false;
        }, 800);

        turnMessageEl.textContent = `💩 ${player.emoji} ${player.name} is being POOPED OUT! 🎉`;
        updatePlayersList();
        updateGameInfo();
        return;
    }

    player.position = newPosition;

    const progress = Math.floor((newPosition / (boardSpaces.length - 1)) * 100);
    let progressMessage = '';
    if (progress < 20) progressMessage = 'in the mouth! 👄';
    else if (progress < 40) progressMessage = 'going down the throat! 🌀';
    else if (progress < 60) progressMessage = 'in the stomach! 💢';
    else if (progress < 80) progressMessage = 'in the intestines! 🧬';
    else progressMessage = 'almost at the end! 💩';

    turnMessageEl.textContent = `${player.emoji} ${player.name} rolled ${roll} and is now ${progressMessage}`;

    renderPlayerBulges();

    const space = boardSpaces[newPosition];
    handleSpaceEffect(player, space);

    updatePlayersList();
    updateGameInfo();

    if (!gameOver && !awaitingDecision) {
        setTimeout(() => {
            nextTurn();
        }, 1200);
    }
}

function handleSpaceEffect(player, space) {
    switch(space.type) {
        case SPACE_TYPES.START:
            turnMessageEl.textContent = `${player.emoji} ${player.name} enters the snake's mouth! 👄`;
            break;

        case SPACE_TYPES.FINISH:
            gameOver = true;
            rollBtn.disabled = true;
            showWinner(player);
            break;

        case SPACE_TYPES.DECISION:
            awaitingDecision = true;
            rollBtn.disabled = true;
            showDecisionModal(player);
            break;

        case SPACE_TYPES.EVENT:
            handleEvent(player);
            break;

        case SPACE_TYPES.POINT:
            const points = randomInt(1, 3);
            player.points += points;
            turnMessageEl.textContent = `${player.emoji} ${player.name} found food and gained ${points} points! 💰`;
            break;

        case SPACE_TYPES.TRUST:
            const trust = randomInt(1, 2);
            player.trust += trust;
            turnMessageEl.textContent = `${player.emoji} ${player.name} helped another rat and gained ${trust} Trust! 🤝`;
            break;

        case SPACE_TYPES.PENALTY:
            handlePenalty(player);
            break;

        case SPACE_TYPES.SPECIAL:
            handleSpecial(player);
            break;

        default:
            break;
    }

    if (player.trust < 0) player.trust = 0;
    renderPlayerBulges();
}

function handleEvent(player) {
    const event = pickRandom(EVENT_SCENARIOS);
    const result = event.action(player);

    if (event.title.includes('Cheese Rain')) {
        players.forEach(p => {
            if (p.id !== player.id) p.points += 2;
        });
        player.points += 2;
        turnMessageEl.textContent = `🧀 ${event.title}! All rats gain 2 points!`;
    } else {
        turnMessageEl.textContent = `${event.title} - ${result}`;
    }

    showEventModal(event.title, result);
    renderPlayerBulges();
    updatePlayersList();
}

function handlePenalty(player) {
    const penalty = randomInt(1, 3);
    const penaltyType = pickRandom(['points', 'trust', 'position']);

    switch(penaltyType) {
        case 'points':
            player.points = Math.max(0, player.points - penalty);
            turnMessageEl.textContent = `${player.emoji} ${player.name} lost ${penalty} points! ⛓️`;
            break;
        case 'trust':
            player.trust = Math.max(0, player.trust - penalty);
            turnMessageEl.textContent = `${player.emoji} ${player.name} lost ${penalty} Trust! ⛓️`;
            break;
        case 'position':
            player.position = Math.max(0, player.position - penalty);
            turnMessageEl.textContent = `${player.emoji} ${player.name} moved back ${penalty} spaces! ⛓️`;
            renderPlayerBulges();
            break;
    }
}

function handleSpecial(player) {
    const bonus = randomInt(1, 4);
    const bonusType = pickRandom(['points', 'trust', 'move']);

    switch(bonusType) {
        case 'points':
            player.points += bonus;
            turnMessageEl.textContent = `${player.emoji} ${player.name} found ${bonus} bonus points! 🎯`;
            break;
        case 'trust':
            player.trust += bonus;
            turnMessageEl.textContent = `${player.emoji} ${player.name} gained ${bonus} Trust! 🎯`;
            break;
        case 'move':
            const move = randomInt(2, 4);
            const newPos = Math.min(boardSpaces.length - 1, player.position + move);
            player.position = newPos;
            turnMessageEl.textContent = `${player.emoji} ${player.name} moved forward ${move} spaces! 🎯`;
            renderPlayerBulges();
            break;
    }
}

function handleDecision(player, optionIndex) {
    const scenario = DECISION_SCENARIOS[player._decisionIndex || 0];
    const option = scenario.options[optionIndex];

    player.points += option.points || 0;
    player.trust += option.trust || 0;

    if (player.trust < 0) player.trust = 0;

    awaitingDecision = false;
    decisionModal.classList.add('hidden');
    rollBtn.disabled = false;

    turnMessageEl.textContent = `${player.emoji} ${player.name}: ${option.text}`;

    renderPlayerBulges();
    updatePlayersList();
    updateGameInfo();

    setTimeout(() => {
        nextTurn();
    }, 800);
}

function nextTurn() {
    if (gameOver) return;

    let nextIndex = (currentPlayerIndex + 1) % players.length;
    let attempts = 0;

    while (attempts < players.length) {
        const nextPlayer = players[nextIndex];
        if (nextPlayer.skipped) {
            nextPlayer.skipped = false;
            turnMessageEl.textContent = `${nextPlayer.emoji} ${nextPlayer.name} was skipped! ⏭️`;
            nextIndex = (nextIndex + 1) % players.length;
        } else {
            break;
        }
        attempts++;
        nextIndex = (nextIndex + 1) % players.length;
    }

    currentPlayerIndex = nextIndex;
    const player = players[currentPlayerIndex];

    updatePlayersList();
    updateGameInfo();
    rollBtn.disabled = false;

    if (!gameOver) {
        turnMessageEl.textContent = `🎮 ${player.emoji} ${player.name}'s turn! Roll the dice!`;
    }
}

// ===== MODALS =====
function showDecisionModal(player) {
    const scenario = pickRandom(DECISION_SCENARIOS);
    player._decisionIndex = DECISION_SCENARIOS.indexOf(scenario);

    decisionTitle.textContent = `❓ ${scenario.title}`;
    decisionDescription.textContent = scenario.description;
    decisionOptions.innerHTML = '';

    scenario.options.forEach((option, index) => {
        const btn = document.createElement('button');
        btn.textContent = option.text;
        btn.addEventListener('click', () => handleDecision(player, index));
        decisionOptions.appendChild(btn);
    });

    decisionModal.classList.remove('hidden');
}

function showEventModal(title, description) {
    eventTitle.textContent = title;
    eventDescription.textContent = description;
    eventModal.classList.remove('hidden');
}

function hideAllModals() {
    decisionModal.classList.add('hidden');
    eventModal.classList.add('hidden');
}

// ===== EVENT LISTENERS =====
rollBtn.addEventListener('click', handleRoll);

newGameBtn.addEventListener('click', async () => {
    const count = getPlayerCount();
    boardContainer.style.display = 'none';
    playersPanel.style.display = 'none';
    introOverlay.classList.remove('hidden');
    await initGame(count);
});

introStartBtn.addEventListener('click', () => {
    // The game already started via initGame
});

eventCloseBtn.addEventListener('click', () => {
    eventModal.classList.add('hidden');
});

poopCloseBtn.addEventListener('click', async () => {
    poopCloseBtn.disabled = true;
    poopCloseBtn.textContent = 'Loading...';
    poopOverlay.classList.add('hidden');

    const count = getPlayerCount();
    boardContainer.style.display = 'none';
    playersPanel.style.display = 'none';
    introOverlay.classList.remove('hidden');
    await initGame(count);
});

// ===== START GAME =====
// Ask for player count first, then start
const initialCount = getPlayerCount();
initGame(initialCount);
