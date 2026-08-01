import { useState } from 'react'
import './TagChipEditor.css'

const TAG_TYPES = ['category', 'budget_tier', 'spec', 'freeform']

export default function TagChipEditor({ tags, onChange }) {
  const [newTagName, setNewTagName] = useState('')
  const [newTagType, setNewTagType] = useState('freeform')

  const removeTag = (index) => {
    onChange(tags.filter((_, i) => i !== index))
  }

  const addTag = () => {
    const name = newTagName.trim().toLowerCase().replace(/\s+/g, '-')
    if (!name) return
    if (tags.some((t) => t.name === name)) return // no duplicates, matches backend dedup
    onChange([...tags, { name, tag_type: newTagType }])
    setNewTagName('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
  }

  return (
    <div className="tag-editor">
      <div className="tag-editor__chips">
        {tags.map((tag, i) => (
          <span key={tag.name} className={`tag-chip tag-chip--${tag.tag_type}`}>
            {tag.name}
            <button type="button" onClick={() => removeTag(i)} aria-label={`Remove ${tag.name}`}>
              ×
            </button>
          </span>
        ))}
        {tags.length === 0 && <span className="tag-editor__empty">No tags yet</span>}
      </div>
      <div className="tag-editor__add">
        <input
          type="text"
          placeholder="Add a tag"
          value={newTagName}
          onChange={(e) => setNewTagName(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <select value={newTagType} onChange={(e) => setNewTagType(e.target.value)}>
          {TAG_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <button type="button" onClick={addTag}>
          Add
        </button>
      </div>
    </div>
  )
}