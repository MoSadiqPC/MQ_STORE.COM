<?php
require 'vendor/autoload.php';

// ضع المفتاح السري الخاص بك هنا
\Stripe\Stripe::setApiKey('sk_test_YOUR_SECRET_KEY');

// معلومات المنتج من موقعك
$product_name = "Elden Ring";
$product_price = 1999; // السعر بالسنتات (19.99$)

// إنشاء جلسة الدفع
$checkout_session = \Stripe\Checkout\Session::create([
    'payment_method_types' => ['card'],
    'line_items' => [[
        'price_data' => [
            'currency' => 'usd',
            'product_data' => [
                'name' => $product_name,
            ],
            'unit_amount' => $product_price,
        ],
        'quantity' => 1,
    ]],
    'mode' => 'payment',
    'success_url' => 'http://your-website.com/success.php', // صفحة النجاح
    'cancel_url' => 'http://your-website.com/cancel.php',   // صفحة الإلغاء
]);

// إعادة توجيه المستخدم إلى صفحة الدفع
header("HTTP/1.1 303 See Other");
header("Location: " . $checkout_session->url);
?>