const reportsModel = require('../models/reports.model');

const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;

async function generateFinancialReport({ page, size } = {}) {
    const pageSize = Math.min(Number(size) || DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE);
    const pageNumber = Math.max(Number(page) || 1, 1);
    const offset = (pageNumber - 1) * pageSize;

    const [courses, total] = await Promise.all([
        reportsModel.findCoursesPage(pageSize, offset),
        reportsModel.countCourses(),
    ]);

    const courseIds = courses.map((course) => course.id);
    const details = await reportsModel.findEnrollmentDetailsForCourses(courseIds);

    const detailsByCourse = new Map();
    for (const row of details) {
        if (!detailsByCourse.has(row.courseId)) detailsByCourse.set(row.courseId, []);
        detailsByCourse.get(row.courseId).push(row);
    }

    const report = courses.map((course) => {
        const rows = detailsByCourse.get(course.id) || [];
        const revenue = rows.reduce((sum, row) => (row.status === 'PAID' ? sum + row.amount : sum), 0);
        const students = rows.map((row) => ({ student: row.studentName || 'Unknown', paid: row.amount || 0 }));
        return { course: course.title, revenue, students };
    });

    return { report, page: pageNumber, size: pageSize, total };
}

module.exports = { generateFinancialReport };
