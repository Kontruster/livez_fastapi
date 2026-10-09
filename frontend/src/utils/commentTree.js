// Утилиты для работы с деревом комментариев.
// Бэкенд отдаёт комментарии уже вложенными (replies), поэтому добавление
// и удаление нужно применять к дереву, а не к плоскому списку.

export function addReply(tree, parentId, reply) {
  if (parentId == null) return [...tree, reply]
  return tree.map((node) => {
    if (node.id === parentId) {
      return { ...node, replies: [...(node.replies || []), reply] }
    }
    return { ...node, replies: addReply(node.replies || [], parentId, reply) }
  })
}

// Удаление комментария убирает и всё его поддерево — так же, как в БД
// (ON DELETE CASCADE у comments.parent_id).
export function removeComment(tree, commentId) {
  return tree
    .filter((node) => node.id !== commentId)
    .map((node) => ({ ...node, replies: removeComment(node.replies || [], commentId) }))
}

export function countComments(tree) {
  return (tree || []).reduce(
    (sum, node) => sum + 1 + countComments(node.replies || []),
    0,
  )
}

export function findComment(tree, commentId) {
  for (const node of tree || []) {
    if (node.id === commentId) return node
    const found = findComment(node.replies || [], commentId)
    if (found) return found
  }
  return null
}
