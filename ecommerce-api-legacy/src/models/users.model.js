const { run, get } = require('../db/database');

async function findByEmail(email) {
    return get('SELECT id FROM users WHERE email = ?', [email]);
}

async function findById(id) {
    return get('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

async function create(name, email, passwordHash) {
    const { lastID } = await run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, passwordHash]
    );
    return lastID;
}

async function deleteById(id) {
    await run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, findById, create, deleteById };
