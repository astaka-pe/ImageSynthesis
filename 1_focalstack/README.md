# Multi-focus Image Fusion

## 0. Depth of Field Fusion

Depth of field (DOF) fusion is a process that combines multiple partially focused images into a single all-in-focus image.

**Input images**

<table>
  <tr>
    <td width="33%">Near focus</td>
    <td width="33%">Mid focus</td>
    <td width="33%">Far focus</td>
  <tr>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/b6761be5-9fcd-40a2-bbdf-431b66032da6.png" width="100%"/></td>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/7a4e49b0-93cc-4324-ac10-d2336d916f1f.png" width="100%"/></td>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/967b0422-ecdb-4d0f-9502-c81bbdd898c1.png" width="100%"/></td>
</table>

**Fusion result**

![fused_pyramid.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/3b95dd1d-a5b8-4e7a-84af-1d37bd7d416e.jpeg)

### 0.1. Depth of Field and Blur

- **Depth of Field (DOF)** is the range of distances in a scene that appear acceptably sharp in an image  
- DOF is mainly determined by the lens aperture (f-number)  
- A shallower DOF leads to stronger blur outside the focus plane  

## 0.2. Focus Breathing

- Even with a prime lens, shifting the focus plane slightly changes the effective focal length and field of view (**focus breathing**)  
- Focusing closer tends to narrow the field of view, while focusing farther tends to widen it  

## 1. Fusion Pipeline

1. Image alignment  
2. Focus map computation  
3. Image fusion  
   1. Weighted average fusion  
   2. Pyramid fusion  

### 1.1. Image Alignment

- Focus breathing causes slight field-of-view changes across images  
- To compensate, an **affine transformation** (scaling, rotation, translation, shear) is estimated and applied  
- The near-focus image (narrowest FOV) is used as the reference, and the other images are aligned to it  

**Alignment result**

- Top: before alignment, Bottom: after alignment  

<table>
  <tr>
    <td width="33%">Near focus</td>
    <td width="33%">Mid focus</td>
    <td width="33%">Far focus</td>
  <tr>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/b6761be5-9fcd-40a2-bbdf-431b66032da6.png" width="100%"/><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/b6761be5-9fcd-40a2-bbdf-431b66032da6.png" width="100%"/></td>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/7a4e49b0-93cc-4324-ac10-d2336d916f1f.png" width="100%"/><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/979a4ac2-1d4b-4839-a9ec-25a01f0b12d3.png" width="100%"/></td>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/967b0422-ecdb-4d0f-9502-c81bbdd898c1.png" width="100%"/><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/f6fa3182-64ae-4537-b78c-e51e44cb40e5.png" width="100%"/></td>
</table>

### 1.2. Focus Map Computation

- Apply a Laplacian filter to each image to evaluate edge strength (degree of sharpness)  
- Apply a Gaussian filter to spread the response and generate a smooth focus map  

<table>
  <tr>
    <td width="33%">Near focus</td>
    <td width="33%">Mid focus</td>
    <td width="33%">Far focus</td>
  <tr>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/b6761be5-9fcd-40a2-bbdf-431b66032da6.png" width="100%"/><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/6264632f-1fd7-4492-b8a6-383a8f373da8.png" width="100%"/></td>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/979a4ac2-1d4b-4839-a9ec-25a01f0b12d3.png" width="100%"/><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/7b3817c1-a786-41f5-a846-afeed4c9077c.png" width="100%"/></td>
    <td width="33%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/f6fa3182-64ae-4537-b78c-e51e44cb40e5.png" width="100%"/><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/f6dbc143-e66a-455f-81d6-d6d5c82b6f4f.png" width="100%"/></td>
</table>

### 1.3. Image Fusion

#### 1.3.1. Weighted Average Fusion (Single-Scale)

- Use focus maps as weights for each input image  
- Compute a weighted average per pixel to obtain an all-in-focus image  

#### 1.3.2. Pyramid Fusion (Multi-Scale)

- Decompose each input image into a Laplacian pyramid  
- Decompose the focus maps into Gaussian pyramids  
- Perform weighted averaging at each scale to build a fused Laplacian pyramid  
- Reconstruct the fused pyramid into the final all-in-focus image  

![image.png](docs/pyramid_fusion.png)

**Fusion results**

- Weighted average fusion may introduce artifacts (e.g., double edges or ghosting around sharp transitions)  
- Pyramid fusion leverages multi-scale information: global structures are fused at coarse levels, while fine details are fused at higher resolutions, reducing artifacts and producing a more natural result  

<table>
  <tr>
    <td width="33%">Weighted average fusion</td>
    <td width="33%">Pyramid fusion</td>
  <tr>
    <td width="50%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/d4a6c371-44db-4da1-a1da-d18470068863.png" width="100%"/></td>
    <td width="50%"><img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/882064/3b95dd1d-a5b8-4e7a-84af-1d37bd7d416e.jpeg" width="100%"/></td>
</table>
