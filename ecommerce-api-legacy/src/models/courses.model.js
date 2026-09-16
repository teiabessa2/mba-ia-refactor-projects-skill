const { get } = require('../db/database');

async function findActiveById(id) {
    return get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]);
}

module.exports = { findActiveById };
