import { Dependency, GraphNode, GraphLink, GraphData } from '@/lib/types'

/**
 * Transforms scan dependencies into D3 graph format
 * Creates a hierarchical graph structure with root, direct, and transitive dependencies
 */
export function transformToGraphData(
  dependencies: Dependency[],
  projectName: string = 'Project'
): GraphData {
  const nodes: GraphNode[] = []
  const links: GraphLink[] = []
  const nodeMap = new Map<string, GraphNode>()

  // Create root node
  const rootNode: GraphNode = {
    id: projectName,
    group: 1, // Root
    status: 'safe',
    data: {
      id: 0,
      package_name: projectName,
      version: '1.0.0',
      ecosystem: 'root',
      is_vulnerable: false,
      cve_count: 0,
      cves: [],
      type: 'direct',
    },
  }
  nodes.push(rootNode)
  nodeMap.set(projectName, rootNode)

  // Separate direct and transitive dependencies
  const directDeps = dependencies.filter((d) => d.type === 'direct' || !d.type)
  const transitiveDeps = dependencies.filter((d) => d.type === 'transitive')

  // Create nodes for direct dependencies
  directDeps.forEach((dep) => {
    const nodeId = `${dep.package_name}@${dep.version}`
    const status = getNodeStatus(dep)

    const node: GraphNode = {
      id: nodeId,
      group: 2, // Direct dependency
      status,
      data: dep,
    }
    nodes.push(node)
    nodeMap.set(nodeId, node)

    // Link to root
    links.push({
      source: projectName,
      target: nodeId,
    })
  })

  // Create nodes for transitive dependencies
  transitiveDeps.forEach((dep) => {
    const nodeId = `${dep.package_name}@${dep.version}`
    const status = getNodeStatus(dep)

    const node: GraphNode = {
      id: nodeId,
      group: 3, // Transitive dependency
      status,
      data: dep,
    }
    nodes.push(node)
    nodeMap.set(nodeId, node)

    // Link to a random direct dependency (simulate transitive relationship)
    // In a real scenario, this would come from the actual dependency tree
    if (directDeps.length > 0) {
      const randomDirect = directDeps[Math.floor(Math.random() * directDeps.length)]
      const parentId = `${randomDirect.package_name}@${randomDirect.version}`
      links.push({
        source: parentId,
        target: nodeId,
      })
    }
  })

  return { nodes, links }
}

/**
 * Determines the status of a node based on its vulnerabilities
 */
function getNodeStatus(dep: Dependency): 'safe' | 'warning' | 'critical' {
  if (!dep.is_vulnerable || dep.cve_count === 0) return 'safe'

  const hasCritical = dep.cves.some(
    (cve) => cve.severity?.toLowerCase() === 'critical' || cve.severity?.toLowerCase() === 'high'
  )

  if (hasCritical) return 'critical'

  const hasWarning = dep.cves.some(
    (cve) => cve.severity?.toLowerCase() === 'medium' || cve.severity?.toLowerCase() === 'low'
  )

  return hasWarning ? 'warning' : 'safe'
}

/**
 * Filters graph data based on selected dependency IDs
 */
export function filterGraphBySelection(
  graphData: GraphData,
  selectedIds: number[]
): GraphData | null {
  if (selectedIds.length === 0) return null

  const selectedPackageNames = new Set<string>()
  graphData.nodes.forEach((node) => {
    if (selectedIds.includes(node.data.id)) {
      selectedPackageNames.add(node.id)
    }
  })

  const filteredNodes = graphData.nodes.filter((node) => selectedPackageNames.has(node.id))
  const filteredNodeIds = new Set(filteredNodes.map((n) => n.id))

  const filteredLinks = graphData.links.filter((link) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id
    const targetId = typeof link.target === 'string' ? link.target : link.target.id
    return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId)
  })

  return { nodes: filteredNodes, links: filteredLinks }
}

/**
 * Calculates basic graph statistics
 */
export function getGraphStats(graphData: GraphData) {
  const totalNodes = graphData.nodes.length
  const criticalNodes = graphData.nodes.filter((n) => n.status === 'critical').length
  const warningNodes = graphData.nodes.filter((n) => n.status === 'warning').length
  const safeNodes = graphData.nodes.filter((n) => n.status === 'safe').length

  return {
    total: totalNodes,
    critical: criticalNodes,
    warning: warningNodes,
    safe: safeNodes,
  }
}
