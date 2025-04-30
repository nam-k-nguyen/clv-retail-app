const express = require('express');
const mysql = require('mysql2');
const path = require('path');

require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Set EJS as the template engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.urlencoded({ extended: true }));


// Connect to Azure MySQL Flexible Server
const db = mysql.createConnection({
  host: 'clv-retail-db.mysql.database.azure.com',
  user: 'admin_user', // full username!
  password: process.env.DB_PASSWORD,
  database: 'retail_data',
  ssl: { rejectUnauthorized: true }
});

// Home route (optional)
app.get('/', (req, res) => {
  res.render('home');
});

app.get('/add', (req, res) => {
  res.render('add'); // one page with all 3 forms
});

// Household 10 data pull route
app.get('/household', (req, res) => {
  const householdId = req.query.id;
  const query = `
    SELECT 
      h.hshd_num,
      t.basket_num,
      t.purchase_date,
      t.product_num,
      p.department,
      p.commodity,
      t.spend,
      t.units,
      t.store_region,
      t.week_num,
      t.year,
      h.loyalty_flag,
      h.age_range,
      h.marital_status,
      h.income_range,
      h.homeowner,
      h.hshd_composition,
      h.hh_size,
      h.children
    FROM transactions t
    JOIN households h ON t.hshd_num = h.hshd_num
    JOIN products p ON t.product_num = p.product_num
    WHERE h.hshd_num = ${householdId}
    ORDER BY h.hshd_num, t.basket_num, t.purchase_date, p.product_num, p.department, p.commodity;
  `;

  db.query(query, [householdId], (err, results) => {
    if (err) {
      console.error(err);
      return res.status(500).send('Error fetching data');
    }
    res.render('household', { data: results, householdId });
  });
});

app.get('/dashboard', async (req, res) => {
  try {
    const [spendBySize] = await db.promise().query(`
      SELECT hh_size, ROUND(AVG(spend), 2) AS avg_spend
      FROM households h
      JOIN transactions t ON h.hshd_num = t.hshd_num
      WHERE hh_size IS NOT NULL
      GROUP BY hh_size
      ORDER BY hh_size
    `);

    const [unitsByBrand] = await db.promise().query(`
      SELECT p.brand_type, SUM(t.units) AS total_units
      FROM transactions t
      JOIN products p ON t.product_num = p.product_num
      GROUP BY p.brand_type
    `);

    const [loyaltySpend] = await db.promise().query(`
      SELECT h.loyalty_flag, ROUND(AVG(t.spend), 2) AS avg_spend
      FROM households h
      JOIN transactions t ON h.hshd_num = t.hshd_num
      WHERE h.loyalty_flag IS NOT NULL
      GROUP BY h.loyalty_flag
    `);

    res.render('dashboard', {
      spendBySize,
      unitsByBrand,
      loyaltySpend
    });
  } catch (err) {
    console.error(err);
    res.status(500).send('Dashboard error');
  }
});



app.post('/add/transaction', (req, res) => {
  const {
    hshd_num, basket_num, purchase_date, product_num,
    spend, units, store_region, week_num, year
  } = req.body;

  const query = `
    INSERT INTO transactions
    (hshd_num, basket_num, purchase_date, product_num, spend, units, store_region, week_num, year)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `;
  db.query(query, [hshd_num, basket_num, purchase_date, product_num, spend, units, store_region, week_num, year], (err) => {
    if (err) return res.status(500).send('Insert failed: ' + err.message);
    res.redirect('/add');
  });
});

app.post('/add/household', (req, res) => {
  const {
    hshd_num, loyalty_flag, age_range, marital_status,
    income_range, homeowner, hshd_composition, hh_size, children
  } = req.body;

  const query = `
    INSERT INTO households
    (hshd_num, loyalty_flag, age_range, marital_status, income_range, homeowner, hshd_composition, hh_size, children)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `;
  db.query(query, [hshd_num, loyalty_flag, age_range, marital_status, income_range, homeowner, hshd_composition, hh_size, children], (err) => {
    if (err) return res.status(500).send('Insert failed: ' + err.message);
    res.redirect('/add');
  });
});

app.post('/add/product', (req, res) => {
  const { product_num, department, commodity, brand_type, natural_organic_flag } = req.body;

  const query = `
    INSERT INTO products (product_num, department, commodity, brand_type, natural_organic_flag)
    VALUES (?, ?, ?, ?, ?)
  `;
  db.query(query, [product_num, department, commodity, brand_type, natural_organic_flag], (err) => {
    if (err) return res.status(500).send('Insert failed: ' + err.message);
    res.redirect('/add');
  });
});



// Start the server
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
