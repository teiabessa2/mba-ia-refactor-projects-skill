const { run } = require('../db/database');

async function create(enrollmentId, amount, status) {
    const { lastID } = await run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]
    );
    return lastID;
}

async function deleteByEnrollmentIds(enrollmentIds) {
    if (enrollmentIds.length === 0) return;
    const placeholders = enrollmentIds.map(() => '?').join(',');
    await run(`DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
}

module.exports = { create, deleteByEnrollmentIds };
