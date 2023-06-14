import React, { useEffect, useState } from 'react';
import { TreeView, TreeItem } from '@mui/lab';
import { Box } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import axios from 'axios';

const FileViewer = () => {
  const [treeData, setTreeData] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    axios.get('/api/folder-tree')
      .then(response => {
        setTreeData(response.data);
      });
  }, []);

  const handleNodeSelect = (event, nodeId) => {
    axios.get(`/api/files/${nodeId}`)
      .then(response => {
        setSelectedFile(response.data);
      });
  };

  const renderTree = (nodes) => (
    <TreeItem key={nodes.id} nodeId={nodes.id} label={nodes.name}>
      {Array.isArray(nodes.children) ? nodes.children.map(node => renderTree(node)) : null}
    </TreeItem>
  );

  return (
    <Box display="flex">
      <Box width="50%">
        <TreeView
          defaultCollapseIcon={<ExpandMoreIcon />}
          defaultExpandIcon={<ChevronRightIcon />}
          onNodeSelect={handleNodeSelect}
        >
          {treeData.map(tree => renderTree(tree))}
        </TreeView>
      </Box>
      <Box width="50%">
        {selectedFile && (
          <img src={`/api/files/${selectedFile.id}`} alt={selectedFile.name} style={{ width: '100%', height: 'auto' }} />
        )}
      </Box>
    </Box>
  );
};

export default FileViewer;
