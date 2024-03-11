class XykmData():
    def __init__(self,
                 xykm,
                 xni,
                 yni,
                 face_node_connectivity_index,
                 iface,
                 inode,
                 xmin,
                 xmax,
                 ymin,
                 ymax,
                 dxi,
                 dyi,
                 xykline,
                 interest_region,
                 sni,
                 nni):
        self.xykm = xykm
        self.xni = xni
        self.yni = yni
        self.face_node_connectivity_index = face_node_connectivity_index
        self.iface = iface
        self.inode = inode
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.dxi = dxi
        self.dyi = dyi
        self.xykline = xykline
        self.interest_region = interest_region
        self.sni = sni
        self.nni = nni