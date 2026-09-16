const usersService = require('../services/users.service');

async function remove(req, res, next) {
    try {
        await usersService.deleteUser(req.params.id);
        res.status(204).send();
    } catch (err) {
        next(err);
    }
}

module.exports = { remove };
