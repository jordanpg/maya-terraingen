import random, math

def distance3D(a, b):
	return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2 + (b[2] - a[2])**2)
	
def cartToSphr(cart, origin=(0,0,0)):
	dX = cart[0] - origin[0]
	dY = cart[1] - origin[1]
	dZ = cart[2] - origin[2]
	
	theta = math.atan2(dX, dZ)
	phi = math.atan2((dZ**2+dX**2)**0.5, dY)
	r = (dX**2 + dY**2 + dZ**2) ** 0.5
	
	return [r,theta,phi]
	
def sphrToCart(sphr, origin=(0,0,0)):
	r = sphr[0]
	theta = sphr[1]
	phi = sphr[2]
	
	x = math.sin(phi) * math.sin(theta) * r + origin[0]
	z = math.sin(phi) * math.cos(theta) * r + origin[2]
	y = math.cos(phi) * r + origin[1]
	
	return [x,y,z]

def boxTransXY(world, aX, aY):
	def _tns(obj, vPos):
		box = cmds.polyEvaluate(obj, b=True)
		xMin = box[aX][0]
		zMin = box[aY][0]
		xBox = box[aX][1] - xMin
		zBox = box[aY][1] - zMin
		
		x = (vPos[aX] - xMin) / xBox + world[0]
		y = (vPos[aY] - zMin) / zBox + world[1]
		z = 0
		return [x, y, None]
	return _tns

def axisMap(map):
	def _tns(obj, vPos):
		return [vPos[map[0]], vPos[map[1]], vPos[map[2]]]
	return _tns

def toSpherical(obj, vPos):
	return cartToSphr(vPos, cmds.xform(obj, ws=True, q=True, t=True))

def constant(val):
	def _rng(obj, vPos):
		return val
	return _rng

def fbm(iter, freq, persist, high, low, seed, world=(0.0,0.0), worldScale=1.0, pre=None, preScale=1, transf=None):
	def _rng(obj, vPos):
		if pre.__class__.__name__ == "function":
			r = pre(obj, vPos) * preScale
		else:
			r = 0
		
		if transf == None:
			wp = boxTransXY(world, 0, 2)(obj, vPos)
		else:
			wp = transf(obj, vPos)
		
		# box = cmds.polyEvaluate(obj, b=True)
		# xMin = box[0][0]
		# zMin = box[2][0]
		# xBox = box[0][1] - xMin
		# zBox = box[2][1] - zMin
		
		# x = (vPos[0] - xMin) / xBox + world[0]
		# y = (vPos[2] - zMin) / zBox + world[1]
		x = wp[0]
		y = wp[1]
		z = wp[2]
		
		maxAmp = 0
		n = 0
		amp = 1
		f = freq
		for i in range(iter):
			if z == None:
				prln = mel.eval("noise(<<" + str(x * f * worldScale) + "," + str(seed) + "," + str(y * f * worldScale) + ">>)")
			else:
				prln = mel.eval("noise(<<" + str(x * f * worldScale) + "," + str(z * f * worldScale) + "," + str(y * f * worldScale) + ">>)")
				prln *= mel.eval("noise(<<" + str(x * f * worldScale) + "," + str(seed) + "," + str(y * f * worldScale) + ">>)")
			n += prln * amp
			maxAmp += amp
			amp *= persist
			f *= 2
			
		n /= maxAmp
		n = n * (high - low) / 2 + (high + low) / 2
		
		return n + r
	return _rng

def tallBiome(fbm, minimum, wScale, effect, seed, world=(0.0,0.0), pre=None, preScale=1, transf=None):
	def _rng(obj, vPos):
		if pre.__class__.__name__ == "function":
			r = pre(obj, vPos) * preScale
		else:
			r = 0
		
		if transf == None:
			wp = boxTransXY(world, 0, 2)(obj, vPos)
		else:
			wp = transf(obj, vPos)
		
		# box = cmds.polyEvaluate(obj, b=True)
		# xMin = box[0][0]
		# zMin = box[2][0]
		# xBox = box[0][1] - xMin
		# zBox = box[2][1] - zMin
		
		# x = (vPos[0] - xMin) / xBox + world[0]
		# y = (vPos[2] - zMin) / zBox + world[1]
		
		bX = wp[0]
		bY = wp[1]
		bZ = wp[2]
		
		n = 0
		if bZ == None:
			n += mel.eval("noise(<<" + str(bX * wScale) + "," + str(seed) + "," + str(bY * wScale) + ">>)") + minimum
		else:
			n += mel.eval("noise(<<" + str(bX * wScale) + "," + str(bZ * wScale) + "," + str(bY * wScale) + ">>)")
			n *= mel.eval("noise(<<" + str(bX * wScale) + "," + str(seed) + "," + str(bY * wScale) + ">>)")
			n += minimum
		
		if n > 1:
			n = 1
		
		return n * effect * fbm(obj, vPos) + r
		
	return _rng

def tVertexColor(colList, func, lvVariance=0, transf=None):
	hList = colList[0]
	cList = colList[1]
	def _rng(obj, vPos):
		h = func(obj, vPos)
		if transf == None:
			y = vPos[1] + h + random.random() * lvVariance
		else:
			y = transf(obj, vPos)[0] + h + random.random() * lvVariance
		#print(y)
		for i in range(len(hList)):
			if y <= hList[i]:
				col = cList[i]
				break
		#print(col)
		cmds.polyColorPerVertex(colorRGB=col)
		
		return h
	return _rng

def centralPeak(peakHt, valleyHt):
	def _rng(obj, vPos):
		oPos = cmds.xform(obj, q=True, ws=True, t=True)
		dist = distance3D(oPos, vPos)
		box = cmds.polyEvaluate(obj, b=True)
		boxMin = [box[0][0], box[1][0], box[2][0]]
		boxMax = [box[0][1], box[1][1], box[2][1]]
		dist /= (distance3D(boxMin, boxMax) / 2)

		mu2 = (1 - math.cos((1 - dist) * math.pi)) / 2
		rng = (valleyHt * (1 - mu2) + peakHt * mu2)
		return ((1 - dist) * random.random() * rng)
		# return (1 - dist) * (peakHt - valleyHt) + valleyHt
	return _rng

def randomizeAxis(obj, axis, tRange):
	verts = cmds.polyEvaluate(obj, v=True)
	for i in range(verts):
		vert = obj + ".vtx[" + str(i) + "]"
		cmds.select(vert)
		tl = [0, 0, 0]
		
		if tRange.__class__.__name__ == "function":
			tl[axis] += tRange(obj, cmds.xform(vert, ws=True, q=True, t=True))
		else:
			tl[axis] += (random.random() - 0.5) * tRange
		cmds.xform(vert, relative=True, t=tl)
		
def randomizeCustom(obj, tlator, tRange):
	verts = cmds.polyEvaluate(obj, v=True)
	for i in range(verts):
		vert = obj + ".vtx[" + str(i) + "]"
		vPos = cmds.xform(vert, ws=True, q=True, t=True)
		cmds.select(vert)
		if tRange.__class__.__name__ == "function":
			tl = tlator(tRange(obj, vPos), obj, vPos)
		else:
			tl = tlator((random.random() - 0.5) * tRange, obj, vPos)
		cmds.xform(vert, t=tl)

def tSpherical(amt, obj, vPos):
	oPos = cmds.xform(obj, ws=True, q=True, t=True)

	sphr = cartToSphr(vPos, oPos)
	sphr[0] += amt

	return sphrToCart(sphr, oPos)

def mainP():
	seed = 58019824
	size = 5.0
	divs = 8
	xRange = range(-4, 6)
	yRange = range(-4, 6)
	maxStep = len(xRange) * len(yRange)
	step = 0
	
	seaLvl = 0.2
	mountainLvl = 1.2
	lvVariance = 0.1
	sandCol = [0.527,0.457,0.162]
	grassCol = [0.091,0.240,0.109]
	mountainCol = [0.278,0.278,0.278]
	colList = [[seaLvl+0.1, mountainLvl, 100], [sandCol, grassCol, mountainCol]]
	objs = []
	print("Generating " + str(max) + " chunks of terrain...")
	for x in xRange:
		for y in yRange:
			step += 1
			pl = cmds.polyPlane(w=size, h=size, sx=divs, sy=divs, ax=(0, 1, 0), cuv=2, ch=1)[0]
			print("Generating chunk " + str((x, y)) + ", step " + str(step) + "/" + str(maxStep))
			cmds.xform(pl, t=(size * x, 0, size * y))
			# randomizeAxis(pl, 1, centralPeak(0.5, 0))
			pos = (x, y)
			# fbm(iter, freq, persist, high, low, seed, world=(0.0,0.0), worldScale=1.0, pre=None, preScale=1)
			octA = fbm(16, 6, 0.4, 3, -1, seed, pos, 0.5)
			octB = fbm(16, 4, 0.2, 1, -1, seed*1.01, pos, 0.4, pre=octA, preScale=0.8)
			octC = fbm(16, 2, 0.1, 0.5, -0.5, seed*1.05, pos, 0.3, pre=octB, preScale=0.8)
			# tallBiome(fbm, minimum, wScale, effect, seed, world=(0.0,0.0), pre=None, preScale=1)
			tallB = tallBiome(octC, 0.1, 0.4, 2, seed, pos)
			randomizeAxis(pl, 1, tVertexColor(colList, tallB, lvVariance))
			
			# cmds.setAttr(pl + ".aiExportColors", 1)
			objs.append(pl)
			cmds.refresh()
	
	g = cmds.group(objs, parent="worldGrp")
	cmds.xform("waterLvl", t=(size / 2.0, seaLvl, size / 2.0))
	cmds.select(g)
	mel.eval("toggleShadeMode")
	cmds.select(d=True)

def recolor():
	size = 5.0
	seaLvl = -0.1
	mountainLvl = 1.1
	sandCol = [0.00, 0.2, 0.6]
	grassCol = [0.091,0.240,0.109]
	mountainCol = [0.278,0.278,0.278]
	colList = [[seaLvl, mountainLvl, 100], [sandCol, grassCol, mountainCol]]

	sel = cmds.ls(sl=True, tr=True)
	maxSteps = len(sel)
	step = 0
	for i in sel:
		step += 1
		print("Recoloring vertices of " + i + "(" + str(step) + "/" + str(maxSteps) + ")")
		randomizeAxis(i, 1, tVertexColor(colList, constant(0)))
		cmds.setAttr(i + ".aiExportColors", 1)
		
	cmds.xform("waterLvl", t=(size / 2.0, seaLvl, size / 2.0))

def mainS():
	rad = 5
	div = 50
	sl = cmds.polySphere(r=rad, sx=div, sy=div, ax=(0, 1, 0), cuv=2, ch=1)
	sphr = sl[0]
	
	seed = 1337
	size = 5.0
	divs = 8
	xRange = range(-4, 6)
	yRange = range(-4, 6)
	maxStep = len(xRange) * len(yRange)
	step = 0
	
	seaLvl = rad - 0.1
	mountainLvl = 0.25 + rad
	snowLvl = 0.5 + rad
	lvVariance = 0
	sandCol = [0.527,0.457,0.162]
	grassCol = [0.091,0.240,0.109]
	mountainCol = [0.278,0.278,0.278]
	snowCap = [0.9, 0.9, 0.9]
	colList = [[seaLvl+0.1, mountainLvl, snowLvl, 100], [sandCol, grassCol, mountainCol, snowCap]]
	
	transNoise = axisMap([0, 1, 2])
	print("Generating topography atop " + sphr)

	# fbm(iter, freq, persist, high, low, seed, world=(0.0,0.0), worldScale=1.0, pre=None, preScale=1, transf=None)
	octA = fbm(16, 6, 0.4, 2, -1, seed, (0, 0), 0.5, transf=transNoise)
	octB = fbm(16, 4, 0.2, 1, -0.5, seed*1.01, (0, 0), 0.4, pre=octA, preScale=0.8, transf=transNoise)
	octC = fbm(16, 2, 0.1, 0.5, -0.25, seed*1.05, (0, 0), 0.3, pre=octB, preScale=0.8, transf=transNoise)
	# tallBiome(fbm, minimum, wScale, effect, seed, world=(0.0,0.0), pre=None, preScale=1)
	tallB = tallBiome(octC, 0.1, 0.4, 2, seed, (0, 0), transf=transNoise)
	randomizeCustom(sphr, tSpherical, tVertexColor(colList, tallB, lvVariance, toSpherical))
	# randomizeCustom(sphr, tSpherical, octA)
	
	g = cmds.group(sphr, parent="worldGrp")
	cmds.xform("waterLvl", t=(size / 2.0, seaLvl, size / 2.0))
	cmds.select(g)
	mel.eval("toggleShadeMode")
	cmds.select(d=True)


# mainP()
# recolor()

mainS()