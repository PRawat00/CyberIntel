'use client'

import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { GraphNode, GraphLink } from '@/lib/types'

interface NetworkGraphProps {
  nodes: GraphNode[]
  links: GraphLink[]
  selectedNodeIds: string[]
  onNodeClick: (node: GraphNode, isMultiSelect: boolean, clickPosition?: { x: number; y: number }) => void
}

/**
 * Calculate gradient color based on vulnerability severity
 * Green (safe) → Yellow (warning) → Orange → Red (critical)
 */
function getSeverityColor(node: GraphNode): string {
  const { data } = node

  // Calculate severity score
  let score = 0
  if (data.cves && data.cves.length > 0) {
    data.cves.forEach((cve) => {
      switch (cve.severity) {
        case 'CRITICAL':
          score += 10
          break
        case 'HIGH':
          score += 5
          break
        case 'MEDIUM':
          score += 2
          break
        case 'LOW':
          score += 1
          break
      }
    })
  }

  // Normalize score to 0-1 range (max score of 50 for gradient calculation)
  const normalizedScore = Math.min(score / 50, 1)

  // Define color stops: green → yellow → orange → red
  const colorScale = d3.scaleLinear<string>()
    .domain([0, 0.3, 0.6, 1])
    .range(['#10b981', '#eab308', '#f97316', '#ef4444']) // green → yellow → orange → red

  return colorScale(normalizedScore)
}

export function NetworkGraph({ nodes, links, selectedNodeIds, onNodeClick }: NetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null)

  // Initial Graph Setup & Draw
  useEffect(() => {
    if (!svgRef.current || !containerRef.current || nodes.length === 0) return

    // If simulation exists, stop it before redrawing
    if (simulationRef.current) simulationRef.current.stop()

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove()

    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight

    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height])
      .attr('style', 'max-width: 100%; height: auto;')

    // Simulation setup
    const simulation = d3
      .forceSimulation<GraphNode>(nodes)
      .force(
        'link',
        d3.forceLink<GraphNode, GraphLink>(links).id((d) => d.id).distance(70)
      )
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(30))

    simulationRef.current = simulation

    // Draw lines
    const link = svg
      .append('g')
      .attr('stroke', '#64748b')  // Explicit slate-500 color
      .attr('stroke-opacity', 0.6)  // Increased from 0.4 for better visibility
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-width', 2)  // Increased from 1.5 for better visibility

    // Draw nodes group
    const nodeGroup = svg
      .append('g')
      .attr('stroke', 'hsl(var(--background))')
      .attr('stroke-width', 1.5)
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node-group')
      .call(
        d3.drag<SVGGElement, GraphNode>()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended) as any
      )

    // Node circles with gradient coloring
    nodeGroup
      .append('circle')
      .attr('r', (d) => (d.group === 1 ? 20 : d.group === 2 ? 12 : 8))
      .attr('fill', (d) => getSeverityColor(d))
      .attr('cursor', 'pointer')
      .attr('class', 'node-circle')
      .style('transition', 'all 0.3s ease')
      .on('click', (event, d) => {
        event.stopPropagation()
        const isMultiSelect = event.ctrlKey || event.metaKey || event.shiftKey
        const clickPosition = { x: event.clientX, y: event.clientY }
        onNodeClick(d, isMultiSelect, clickPosition)
      })
      .on('mouseenter', function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', (d: any) => (d.group === 1 ? 24 : d.group === 2 ? 14 : 10))
      })
      .on('mouseleave', function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', (d: any) => (d.group === 1 ? 20 : d.group === 2 ? 12 : 8))
      })

    // Labels
    nodeGroup
      .append('text')
      .text((d) => (d.group <= 2 ? d.id : ''))
      .attr('x', 15)
      .attr('y', 4)
      .attr('fill', 'hsl(var(--muted-foreground))')
      .style('font-size', '10px')
      .style('pointer-events', 'none')

    nodeGroup.append('title').text((d) => `${d.id}\nStatus: ${d.status}`)

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as GraphNode).x!)
        .attr('y1', (d) => (d.source as GraphNode).y!)
        .attr('x2', (d) => (d.target as GraphNode).x!)
        .attr('y2', (d) => (d.target as GraphNode).y!)

      nodeGroup.attr('transform', (d) => `translate(${d.x},${d.y})`)
    })

    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event: any) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    return () => {
      simulation.stop()
    }
  }, [nodes, links, onNodeClick])

  // Separate effect for selection styling to avoid resetting simulation
  useEffect(() => {
    if (!svgRef.current) return

    const svg = d3.select(svgRef.current)

    svg
      .selectAll('.node-group circle')
      .attr('stroke', (d: any) =>
        selectedNodeIds.includes(d.id) ? 'hsl(var(--primary))' : 'hsl(var(--background))'
      )
      .attr('stroke-width', (d: any) => (selectedNodeIds.includes(d.id) ? 3 : 1.5))
      .attr('stroke-opacity', (d: any) => (selectedNodeIds.includes(d.id) ? 1 : 0.8))
      .style('filter', (d: any) =>
        selectedNodeIds.includes(d.id) ? 'drop-shadow(0 0 6px hsl(var(--primary)))' : 'none'
      )
  }, [selectedNodeIds])

  return (
    <div
      ref={containerRef}
      className="w-full h-full rounded-lg overflow-hidden bg-card shadow-inner border relative"
    >
      <svg ref={svgRef} className="w-full h-full block"></svg>
      <div className="absolute bottom-4 right-4 bg-card/80 p-3 rounded-lg text-xs text-muted-foreground border backdrop-blur-sm pointer-events-none select-none">
        <div className="font-semibold mb-2 text-slate-300">Severity Gradient</div>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#10b981' }}></span>
          <span>Safe</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#eab308' }}></span>
          <span>Low Risk</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#f97316' }}></span>
          <span>High Risk</span>
        </div>
        <div className="flex items-center gap-2 mb-2">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ef4444' }}></span>
          <span>Critical</span>
        </div>
        <div className="text-[10px] opacity-60 pt-2 border-t">
          <div>Click: Select node</div>
          <div>Ctrl/Cmd+Click: Multi-select</div>
          <div>Drag: Move node</div>
        </div>
      </div>
    </div>
  )
}
