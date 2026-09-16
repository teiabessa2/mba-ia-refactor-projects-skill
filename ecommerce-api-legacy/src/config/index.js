require('dotenv').config();

const config = {
    port: Number(process.env.PORT) || 3000,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    adminApiKey: process.env.ADMIN_API_KEY,
};

module.exports = config;
