import { useEffect, useMemo, useRef, useState } from "react";
import { forceCenter, forceLink, forceManyBody, forceSimulation } from "d3-force";

type GraphNode = { id: string; degree: number };
type GraphEdge = { source: string; target: string; weight: number };

export function ForceGraph({
  nodes,
  edges,
  selectedWord,
  onWordClick
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedWord?: string;
  onWordClick?: (word: string) => void;
}) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 420 });

  const { sampledNodes, sampledEdges } = useMemo(() => {
    const cleanNodes = nodes
      .filter((node) => /[\u4e00-\u9fff]/.test(node.id))
      .sort((a, b) => b.degree - a.degree)
      .slice(0, 120);
    const idSet = new Set(cleanNodes.map((node) => node.id));
    const cleanEdges = edges
      .filter((edge) => idSet.has(edge.source) && idSet.has(edge.target))
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 220);
    return { sampledNodes: cleanNodes, sampledEdges: cleanEdges };
  }, [nodes, edges]);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const nextWidth = Math.max(360, Math.floor(entry.contentRect.width));
      const nextHeight = Math.max(300, Math.floor(entry.contentRect.height));
      setDimensions((prev) => {
        if (prev.width === nextWidth && prev.height === nextHeight) return prev;
        return { width: nextWidth, height: nextHeight };
      });
    });
    observer.observe(svg);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || sampledNodes.length === 0) return;
    const width = dimensions.width;
    const height = dimensions.height;
    const padding = 24;

    const nodesLocal = sampledNodes.map((n) => ({ ...n, x: width / 2, y: height / 2 }));
    const linksLocal = sampledEdges.map((e) => ({ ...e }));

    const sim = forceSimulation(nodesLocal as never[])
      .force(
        "link",
        forceLink(linksLocal as never[])
          .id((d: any) => d.id)
          .distance((l: { weight: number }) => Math.max(30, 110 - l.weight * 3))
      )
      .force("charge", forceManyBody().strength(-120))
      .force("center", forceCenter(width / 2, height / 2))
      .alpha(1);

    const lines = Array.from(svg.querySelectorAll<SVGLineElement>("[data-role='edge']"));
    const circles = Array.from(svg.querySelectorAll<SVGCircleElement>("[data-role='node']"));
    const labels = Array.from(svg.querySelectorAll<SVGTextElement>("[data-role='label']"));

    sim.on("tick", () => {
      lines.forEach((line, idx) => {
        const edge = linksLocal[idx] as unknown as {
          source: { x: number; y: number };
          target: { x: number; y: number };
        };
        line.setAttribute("x1", `${edge.source.x ?? 0}`);
        line.setAttribute("y1", `${edge.source.y ?? 0}`);
        line.setAttribute("x2", `${edge.target.x ?? 0}`);
        line.setAttribute("y2", `${edge.target.y ?? 0}`);
      });
      circles.forEach((circle, idx) => {
        const node = nodesLocal[idx] as { x: number; y: number };
        node.x = Math.max(padding, Math.min(width - padding, node.x ?? width / 2));
        node.y = Math.max(padding, Math.min(height - padding, node.y ?? height / 2));
        circle.setAttribute("cx", `${node.x}`);
        circle.setAttribute("cy", `${node.y}`);
      });
      labels.forEach((label, idx) => {
        const node = nodesLocal[idx] as { x: number; y: number };
        label.setAttribute("x", `${(node.x ?? 0) + 8}`);
        label.setAttribute("y", `${(node.y ?? 0) + 4}`);
      });
    });

    return () => {
      sim.stop();
    };
  }, [dimensions.height, dimensions.width, sampledNodes, sampledEdges]);

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
      className="h-[420px] w-full rounded-xl border border-border bg-panelMuted"
    >
      {sampledEdges.map((edge, idx) => (
        <line
          key={`${edge.source}-${edge.target}-${idx}`}
          data-role="edge"
          stroke="rgba(148,163,184,0.22)"
          strokeWidth={Math.min(2.6, 0.5 + edge.weight * 0.1)}
        />
      ))}
      {sampledNodes.map((node, idx) => {
        const active = selectedWord === node.id;
        return (
          <g key={`${node.id}-${idx}`} className="cursor-pointer" onClick={() => onWordClick?.(node.id)}>
            <circle
              data-role="node"
              r={Math.max(4, Math.min(16, node.degree / 8))}
              fill={active ? "#f59e0b" : "#38bdf8"}
              opacity={active ? 1 : 0.8}
            />
            <text data-role="label" fill={active ? "#f8fafc" : "#cbd5e1"} fontSize="11">
              {node.id}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

