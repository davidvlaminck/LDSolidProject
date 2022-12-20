html_template_string = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<title>Visualizing RDF using D3</title>
	<meta name="author" content="Rathachai CHAWUTHAI">
	
	<style type="text/css">
		.node {
		  stroke: #fff;
		  fill:#ddd;
		  stroke-width: 1.5px;
		}

		.link {
		  stroke: #999;
		  stroke-opacity: .6;
		  stroke-width: 1px;
		}

		marker {
			stroke: #999;
			fill:rgba(124,240,10,0);
		}

		.node-text {
		  font: 11px sans-serif;
		  fill:black;
		}

		.link-text {
		  font: 9px sans-serif;
		  fill:grey;
		}
		
		svg{
			border:1px solid black;
		}
	</style>
	
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
	<script src="http://d3js.org/d3.v3.min.js"></script>
	<script>
		function filterNodesById(nodes,id){
			return nodes.filter(function(n) { return n.id === id; });
		}
		
		function triplesToGraph(triples){
		
			svg.html("");
			//Graph
			var graph={nodes:[], links:[]};
			
			//Initial Graph from triples
			triples.forEach(function(triple){
				var subjId = triple.subject;
				var predId = triple.predicate;
				var objId = triple.object;
				
				var subjNode = filterNodesById(graph.nodes, subjId)[0];
				var objNode  = filterNodesById(graph.nodes, objId)[0];
				
				if(subjNode==null){
					subjNode = {id:subjId, label:subjId, weight:1};
					graph.nodes.push(subjNode);
				}
				
				if(objNode==null){
					objNode = {id:objId, label:objId, weight:1};
					graph.nodes.push(objNode);
				}
			
				
				graph.links.push({source:subjNode, target:objNode, predicate:predId, weight:1});
			});
			
			return graph;
		}
		
		
		function update(){
			// ==================== Add Marker ====================
			svg.append("svg:defs").selectAll("marker")
			    .data(["end"])
			  .enter().append("svg:marker")
			    .attr("id", String)
			    .attr("viewBox", "0 -5 10 10")
			    .attr("refX", 30)
			    .attr("refY", -0.5)
			    .attr("markerWidth", 6)
			    .attr("markerHeight", 6)
			    .attr("orient", "auto")
			  .append("svg:polyline")
			    .attr("points", "0,-5 10,0 0,5")
			    ;
				
			// ==================== Add Links ====================
			var links = svg.selectAll(".link")
								.data(graph.links)
								.enter()
								.append("line")
									.attr("marker-end", "url(#end)")
									.attr("class", "link")
									.attr("stroke-width",1)
							;//links
			
			// ==================== Add Link Names =====================
			var linkTexts = svg.selectAll(".link-text")
		                .data(graph.links)
		                .enter()
		                .append("text")
							.attr("class", "link-text")
							.text( function (d) { return d.predicate; })
						;

				//linkTexts.append("title")
				//		.text(function(d) { return d.predicate; });
						
			// ==================== Add Link Names =====================
			var nodeTexts = svg.selectAll(".node-text")
		                .data(graph.nodes)
		                .enter()
		                .append("text")
							.attr("class", "node-text")
							.text( function (d) { return d.label; })
						;

				//nodeTexts.append("title")
				//		.text(function(d) { return d.label; });
			
			// ==================== Add Node =====================
			var nodes = svg.selectAll(".node")
								.data(graph.nodes)
								.enter()
								.append("circle")
									.attr("class", "node")
									.attr("r",8)
									.call(force.drag)
							;//nodes
		
			// ==================== Force ====================
			force.on("tick", function() {
				nodes
					.attr("cx", function(d){ return d.x; })
					.attr("cy", function(d){ return d.y; })
					;
				
				links
					.attr("x1", 	function(d)	{ return d.source.x; })
			        .attr("y1", 	function(d) { return d.source.y; })
			        .attr("x2", 	function(d) { return d.target.x; })
			        .attr("y2", 	function(d) { return d.target.y; })
			       ;
				   
				nodeTexts
					.attr("x", function(d) { return d.x + 12 ; })
					.attr("y", function(d) { return d.y + 3; })
					;
					

				linkTexts
					.attr("x", function(d) { return 4 + (d.source.x + d.target.x)/2  ; })
					.attr("y", function(d) { return 4 + (d.source.y + d.target.y)/2 ; })
					;
			});
			
			// ==================== Run ====================
			force
		      .nodes(graph.nodes)
		      .links(graph.links)
			  .charge(-500)
			  .linkDistance(100)
		      .start()
			  ;
		}
		
		
	</script>
</head>
<body style="margin:20px;">
  <div id="svg-body" class="panel-body"></div>
  <script>
  	var triples = [
  	        $$$triples$$$
  		];
		
	var svg = d3.select("#svg-body").append("svg")
				.attr("width", 1800)
				.attr("height", 800)
				;
				
	var force = d3.layout.force().size([1800, 800]);
	
	var graph = triplesToGraph(triples);
	
	update();
	
  </script>
  
<p>Time spent to perform query: found $triple_count$ triples in $time_spent$ seconds</p>
  <footer style="padding:20px; height:50px; border-top:1px solid #eee; background:#fafafa; text-align:center">
	By: <strong>Rathachai Chawuthai</strong>
	<br/>
	<a target="_blank" href="https://github.com/Rathachai">GitHub</a> | <a target="_blank" href="https://www.linkedin.com/in/rathachai">LinkedIn</a>
  </footer>
</body>"""
