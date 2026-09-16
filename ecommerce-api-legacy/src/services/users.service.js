const usersModel = require('../models/users.model');
const enrollmentsModel = require('../models/enrollments.model');
const paymentsModel = require('../models/payments.model');
const { AppError } = require('../utils/errors');

async function deleteUser(userId) {
    const user = await usersModel.findById(userId);
    if (!user) throw new AppError('Usuário não encontrado', 404);

    const enrollmentIds = await enrollmentsModel.findIdsByUserId(userId);
    await paymentsModel.deleteByEnrollmentIds(enrollmentIds);
    await enrollmentsModel.deleteByUserId(userId);
    await usersModel.deleteById(userId);
}

module.exports = { deleteUser };
