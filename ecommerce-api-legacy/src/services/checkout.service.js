const bcrypt = require('bcryptjs');
const usersModel = require('../models/users.model');
const coursesModel = require('../models/courses.model');
const enrollmentsModel = require('../models/enrollments.model');
const paymentsModel = require('../models/payments.model');
const auditLogsModel = require('../models/auditLogs.model');
const logger = require('../utils/logger');
const { AppError } = require('../utils/errors');

const DEFAULT_PASSWORD = '123456';

function authorizePayment(card) {
    // Mock gateway authorization — no real provider integrated yet.
    return card.startsWith('4') ? 'PAID' : 'DENIED';
}

async function checkout({ username, email, password, courseId, card }) {
    if (!username || !email || !courseId || !card) {
        throw new AppError('Bad Request', 400);
    }

    const course = await coursesModel.findActiveById(courseId);
    if (!course) throw new AppError('Curso não encontrado', 404);

    const existingUser = await usersModel.findByEmail(email);
    let userId;
    if (existingUser) {
        userId = existingUser.id;
    } else {
        const passwordHash = await bcrypt.hash(password || DEFAULT_PASSWORD, 12);
        userId = await usersModel.create(username, email, passwordHash);
    }

    logger.info({ courseId, userId }, 'Processando pagamento');
    const status = authorizePayment(card);
    if (status === 'DENIED') throw new AppError('Pagamento recusado', 400);

    const enrollmentId = await enrollmentsModel.create(userId, courseId);
    await paymentsModel.create(enrollmentId, course.price, status);
    await auditLogsModel.create(`Checkout curso ${courseId} por ${userId}`);

    logger.info({ userId, courseTitle: course.title }, 'Checkout concluído');

    return { enrollmentId };
}

module.exports = { checkout };
