const checkoutService = require('../services/checkout.service');

async function checkout(req, res, next) {
    try {
        const { usr, eml, pwd, c_id, card } = req.body;
        const result = await checkoutService.checkout({
            username: usr,
            email: eml,
            password: pwd,
            courseId: c_id,
            card,
        });
        res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
