import express from 'express';
const app = express();
app.use(express.urlencoded({ extended: true }));

app.get('/', (req, res) => {
    res.send(`
    <h2>Register</h2>
    <form method="POST">
      <input name="username" placeholder="Username" required /><br/>
      <input name="password" type="password" placeholder="Password" required /><br/>
      <input name="email" type="email" placeholder="Email" required /><br/>
      <button type="submit">Submit</button>
    </form>
  `);
});

app.post('/', (req, res) => {
    console.log(req.body);
    res.send('Thank you for registering!');
});

app.listen(process.env.PORT || 3000, () => console.log('Server running'));
