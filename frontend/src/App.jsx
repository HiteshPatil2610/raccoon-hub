import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home.jsx'
import ProductDetail from './pages/ProductDetail.jsx'
import AdminPanel from './pages/AdminPanel.jsx'
import './App.css'

export default function App() {
  return (
    <>
      <header className="app-header">
        <Link to="/" className="app-header__logo">
          Raccoon Hub
        </Link>
        <nav>
          <Link to="/">Shop</Link>
          <Link to="/admin">Admin</Link>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/product/:asin" element={<ProductDetail />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </main>
    </>
  )
}