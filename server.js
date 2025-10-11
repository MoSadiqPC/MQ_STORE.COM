// server.js - الكود الموحد والنهائي

const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors'); 
const path = require('path');
const bcrypt = require('bcryptjs'); 

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json()); 
app.use(express.urlencoded({ extended: true })); 
app.use(express.static(__dirname)); 

const dbPath = path.resolve(__dirname, 'database.db');
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) { console.error('Error connecting to database:', err.message); } 
    else { console.log('Connected to the SQLite database.'); initializeDatabase(); }
});

function initializeDatabase() {
    db.serialize(() => {
        db.run(`CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, 
            category TEXT NOT NULL, price REAL, discount INTEGER, shop_url TEXT NOT NULL, image_url TEXT          
        )`);
        db.run(`CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, 
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user'
        )`, async (err) => {
            if (err) return;
            const defaultUsername = 'admin_diniro';
            const defaultPassword = 'secure_password'; 
            db.get("SELECT * FROM users WHERE username = ?", [defaultUsername], async (err, row) => {
                if (!row) {
                    const hashedPassword = await bcrypt.hash(defaultPassword, 10);
                    db.run("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", [defaultUsername, hashedPassword, 'admin']);
                    console.log(`Default Admin User created: ${defaultUsername} / ${defaultPassword}`);
                }
            });
        });

        // إدخال البيانات الافتراضية للألعاب
        const initialGames = [
            { name: "Elden Ring", category: "rpg", price: 49.99, discount: 60, url: "our-shop.html#eldenring", image: "EldenRing.jpg" },
            { name: "Cyberpunk 2077", category: "rpg", price: 39.99, discount: 55, url: "our-shop.html#cyberpunk", image: "Cyberpunk.jpg" },
            { name: "Civilization VI", category: "strategy", price: 39.99, discount: 65, url: "our-shop.html#civilization6", image: "Civilization.jpg" },
            { name: "Forza Horizon 5", category: "racing", price: 29.99, discount: 50, url: "our-shop.html#forza5", image: "Forza.jpg" },
            { name: "Dota 2", category: "strategy", price: 0.00, discount: 100, url: "GIT NOW.html#dota2", image: "Dota2.jpg" },
            { name: "Warframe", category: "shooter", price: 0.00, discount: 100, url: "GIT NOW.html#warframe", image: "Warframe.jpg" },
            { name: "Path of Exile", category: "rpg", price: 0.00, discount: 100, url: "GIT NOW.html#pathofexile", image: "PathOfExile.jpg" },
            { name: "Team Fortress 2", category: "shooter", price: 0.00, discount: 100, url: "GIT NOW.html#teamfortress2", image: "TeamFortress2.jpg" },
        ];
        initialGames.forEach(game => {
            db.run("INSERT OR IGNORE INTO games (name, category, price, discount, shop_url, image_url) VALUES (?, ?, ?, ?, ?, ?)", 
                [game.name, game.category, game.price, game.discount, game.url, game.image]);
        });
    });
}

// ----------------------------------------------------
// واجهات API
// ----------------------------------------------------

app.post('/api/auth/login', async (req, res) => { /* Admin login logic */ });
app.post('/api/auth/userlogin', async (req, res) => {
    const { username, password } = req.body;
    db.get("SELECT password_hash FROM users WHERE username = ? AND role = 'user'", [username], async (err, row) => {
        if (!row) return res.status(401).json({ success: false, message: 'Invalid username or password.' });
        const match = await bcrypt.compare(password, row.password_hash);
        if (match) res.json({ success: true, message: 'User login successful.', username });
        else res.status(401).json({ success: false, message: 'Invalid username or password.' });
    });
});
app.post('/api/auth/register', async (req, res) => { /* Registration logic */ });
app.get('/api/games', (req, res) => {
    db.all("SELECT * FROM games ORDER BY id DESC", [], (err, rows) => {
        if (err) return res.status(500).json({ "error": err.message });
        res.json({ "message": "success", "data": rows });
    });
});
app.get('/api/game/:hash', (req, res) => {
    const gameHash = req.params.hash;
    db.get("SELECT * FROM games WHERE shop_url LIKE ? LIMIT 1", [`%#${gameHash}`], (err, row) => {
        if (row) res.json({ "message": "success", "data": row });
        else res.status(404).json({ "message": "Game not found." });
    });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Default Admin: admin_diniro / secure_password`);
});