import { useEffect, useState, useCallback, useRef } from 'react'
import { LayoutGroup } from 'motion/react'
import { Search } from 'lucide-react'
import ProductCard from '../components/ProductCard.jsx'
import { api } from '../api/client.js'
import './Home.css'

const PAGE_SIZE = 24

// Tag type display labels and sort order
const TAG_TYPE_LABELS = {
  category: 'Category',
  budget_tier: 'Budget',
  spec: 'Spec',
  freeform: 'Style',
}
const TAG_TYPE_ORDER = ['category', 'budget_tier', 'spec', 'freeform']

function groupTagsByType(tags) {
  const groups = {}
  for (const t of tags) {
    if (!groups[t.tag_type]) groups[t.tag_type] = []
    groups[t.tag_type].push(t)
  }
  return groups
}

export default function Home() {
  const [products, setProducts] = useState([])
  const [tags, setTags] = useState([])
  const [activeTag, setActiveTag] = useState('')
  const [sort, setSort] = useState('newest')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedAsin, setExpandedAsin] = useState(null)
  const debounceRef = useRef(null)

  // Load tags once
  useEffect(() => {
    api.listTags().then(setTags).catch(() => {})
  }, [])

  // Debounce search input
  const handleSearchInput = (val) => {
    setSearchInput(val)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setSearch(val)
      setPage(0)
    }, 300)
  }

  // Reset page when filters/sort change
  useEffect(() => { setPage(0) }, [activeTag, sort, search])

  // Fetch products + total count
  useEffect(() => {
    setLoading(true)
    setError('')
    const params = {
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      sort,
      ...(activeTag ? { tag: activeTag } : {}),
      ...(search.trim() ? { search: search.trim() } : {}),
    }
    Promise.all([api.listProducts(params), api.countProducts(params)])
      .then(([prods, countRes]) => {
        setProducts(prods)
        setTotal(countRes.total)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [activeTag, sort, search, page])

  const toggleExpand = (asin) =>
    setExpandedAsin((prev) => (prev === asin ? null : asin))

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const tagGroups = groupTagsByType(tags)

  return (
    <div className="home">
      <div className="home__header">
        <h1>Raccoon Hub</h1>
        <p>Hand-picked gear, straight to Amazon.</p>
      </div>

      <div className="home__toolbar">
        {/* Search */}
        <div className="home__search">
          <Search className="home__search-icon" />
          <input
            type="text"
            placeholder="Search products…"
            value={searchInput}
            onChange={(e) => handleSearchInput(e.target.value)}
            className="home__search-input"
          />
        </div>

        {/* Sort */}
        <div className="home__sort">
          <label htmlFor="sort-select">Sort</label>
          <select
            id="sort-select"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="newest">Newest</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="rating">Top Rated</option>
          </select>
        </div>
      </div>

      <div className="home__body">
        {/* Tag sidebar */}
        {tags.length > 0 && (
          <aside className="home__sidebar">
            <div className="home__sidebar-section">
              <button
                className={`home__sidebar-all ${activeTag === '' ? 'is-active' : ''}`}
                onClick={() => { setActiveTag(''); setPage(0) }}
              >
                All products
                <span className="home__tag-count">{total}</span>
              </button>
            </div>

            {TAG_TYPE_ORDER.filter((t) => tagGroups[t]).map((type) => (
              <div key={type} className="home__sidebar-section">
                <p className="home__sidebar-heading">{TAG_TYPE_LABELS[type]}</p>
                {tagGroups[type].map((t) => (
                  <button
                    key={t.name}
                    className={`home__sidebar-tag ${activeTag === t.name ? 'is-active' : ''}`}
                    onClick={() => { setActiveTag(t.name); setPage(0) }}
                  >
                    {t.name}
                    {t.product_count != null && (
                      <span className="home__tag-count">{t.product_count}</span>
                    )}
                  </button>
                ))}
              </div>
            ))}
          </aside>
        )}

        {/* Product grid */}
        <div className="home__content">
          {loading && <p className="home__status">Loading products…</p>}
          {error && <p className="home__status home__status--error">{error}</p>}
          {!loading && !error && products.length === 0 && (
            <p className="home__status">No products found.</p>
          )}

          <LayoutGroup>
            <div className="home__grid">
              {products.map((p) => (
                <ProductCard
                  key={p.id}
                  product={p}
                  isExpanded={expandedAsin === p.asin}
                  onToggleExpand={() => toggleExpand(p.asin)}
                />
              ))}
            </div>
          </LayoutGroup>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="home__pagination">
              <button
                className="home__page-btn"
                onClick={() => setPage((p) => p - 1)}
                disabled={page === 0}
              >
                ← Prev
              </button>
              <span className="home__page-info">
                Page {page + 1} of {totalPages}
              </span>
              <button
                className="home__page-btn"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= totalPages - 1}
              >
                Next →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
