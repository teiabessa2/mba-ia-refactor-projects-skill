const { get, all } = require('../db/database');

async function findCoursesPage(limit, offset) {
    return all('SELECT id, title FROM courses ORDER BY id LIMIT ? OFFSET ?', [limit, offset]);
}

async function countCourses() {
    const row = await get('SELECT COUNT(*) AS total FROM courses');
    return row.total;
}

async function findEnrollmentDetailsForCourses(courseIds) {
    if (courseIds.length === 0) return [];
    const placeholders = courseIds.map(() => '?').join(',');
    return all(
        `SELECT e.course_id AS courseId,
                u.name AS studentName,
                p.amount AS amount,
                p.status AS status
         FROM enrollments e
         LEFT JOIN users u ON u.id = e.user_id
         LEFT JOIN payments p ON p.enrollment_id = e.id
         WHERE e.course_id IN (${placeholders})`,
        courseIds
    );
}

module.exports = { findCoursesPage, countCourses, findEnrollmentDetailsForCourses };
