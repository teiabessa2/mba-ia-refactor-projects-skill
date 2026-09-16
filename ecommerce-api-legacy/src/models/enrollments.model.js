const { run, all } = require('../db/database');

async function create(userId, courseId) {
    const { lastID } = await run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, courseId]
    );
    return lastID;
}

async function findIdsByUserId(userId) {
    const rows = await all('SELECT id FROM enrollments WHERE user_id = ?', [userId]);
    return rows.map((row) => row.id);
}

async function deleteByUserId(userId) {
    await run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
}

module.exports = { create, findIdsByUserId, deleteByUserId };
