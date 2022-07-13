import cv2
import numpy as np
import torch
from PIL import Image
from captum.attr import visualization
import TransformerExplainability.CLIP.clip as clip
from TransformerExplainability.CLIP.clip.simple_tokenizer import SimpleTokenizer as _Tokenizer
_tokenizer = _Tokenizer()

start_layer = -1
start_layer_text = -1
# start_layer =  1
# #start_layer_text =  -1

def interpret(image, texts, model, device, start_layer = start_layer, start_layer_text = start_layer_text):
	batch_size = texts.shape[0]
	images = image.repeat(batch_size, 1, 1, 1)
	logits_per_image, logits_per_text = model(images, texts)

	#probs = logits_per_image.softmax(dim=-1).detach().cpu().numpy()

	index = [i for i in range(batch_size)]
	one_hot = np.zeros((logits_per_image.shape[0], logits_per_image.shape[1]), dtype=np.float32)
	one_hot[torch.arange(logits_per_image.shape[0]), index] = 1
	one_hot = torch.from_numpy(one_hot).requires_grad_(True)
	one_hot = torch.sum(one_hot.cuda() * logits_per_image)
	model.zero_grad()

	image_attn_blocks = list(dict(model.visual.transformer.resblocks.named_children()).values())

	if start_layer == -1:
		# calculate index of last layer
		start_layer = len(image_attn_blocks) - 1

	num_tokens = image_attn_blocks[0].attn_probs.shape[-1]
	R = torch.eye(num_tokens, num_tokens, dtype=image_attn_blocks[0].attn_probs.dtype).to(device)
	R = R.unsqueeze(0).expand(batch_size, num_tokens, num_tokens)
	for i, blk in enumerate(image_attn_blocks):
		if i < start_layer:
			continue
		grad = torch.autograd.grad(one_hot, [blk.attn_probs], retain_graph=True)[0].detach()
		cam = blk.attn_probs.detach()
		cam = cam.reshape(-1, cam.shape[-1], cam.shape[-1])
		grad = grad.reshape(-1, grad.shape[-1], grad.shape[-1])
		cam = grad * cam
		cam = cam.reshape(batch_size, -1, cam.shape[-1], cam.shape[-1])
		cam = cam.clamp(min=0).mean(dim=1)
		R = R + torch.bmm(cam, R)
	image_relevance = R[:, 0, 1:]

	text_attn_blocks = list(dict(model.transformer.resblocks.named_children()).values())

	if start_layer_text == -1:
		# calculate index of last layer
		start_layer_text = len(text_attn_blocks) - 1

	num_tokens = text_attn_blocks[0].attn_probs.shape[-1]
	R_text = torch.eye(num_tokens, num_tokens, dtype=text_attn_blocks[0].attn_probs.dtype).to(device)
	R_text = R_text.unsqueeze(0).expand(batch_size, num_tokens, num_tokens)
	for i, blk in enumerate(text_attn_blocks):
		if i < start_layer_text:
			continue
		grad = torch.autograd.grad(one_hot, [blk.attn_probs], retain_graph=True)[0].detach()
		cam = blk.attn_probs.detach()
		cam = cam.reshape(-1, cam.shape[-1], cam.shape[-1])
		grad = grad.reshape(-1, grad.shape[-1], grad.shape[-1])
		cam = grad * cam
		cam = cam.reshape(batch_size, -1, cam.shape[-1], cam.shape[-1])
		cam = cam.clamp(min=0).mean(dim=1)
		R_text = R_text + torch.bmm(cam, R_text)
	text_relevance = R_text

	return logits_per_image, logits_per_text, text_relevance, image_relevance

def clamp(num, min_value, max_value):
	return max(min(num, max_value), min_value)

def show_image_relevance(image_relevance, image, score):
	score = clamp(score, 20, 30)
	score -= 20
	score /= 10
	score /= 2
	score += 0.5

	# create heatmap from mask on image
	def show_cam_on_image(img, mask):
		heatmap = cv2.applyColorMap(np.uint8(255 * mask * score), cv2.COLORMAP_JET)
		heatmap = np.float32(heatmap) / 255
		cam = heatmap + np.float32(img)
		cam = cam / np.max(cam)
		return cam

	dim = int(image_relevance.numel() ** 0.5)
	image_relevance = image_relevance.reshape(1, 1, dim, dim)
	image_relevance = torch.nn.functional.interpolate(image_relevance, size=224, mode="bicubic")
	image_relevance = image_relevance.reshape(224, 224).cuda().data.cpu().numpy()
	image_relevance = (image_relevance - image_relevance.min()) / (image_relevance.max() - image_relevance.min())
	image = image[0].permute(1, 2, 0).data.cpu().numpy()
	image = (image - image.min()) / (image.max() - image.min())
	vis = show_cam_on_image(image, image_relevance)
	vis = np.uint8(255 * vis)
	vis = cv2.cvtColor(np.array(vis), cv2.COLOR_RGB2BGR)

	return vis



def show_heatmap_on_text(text, text_encoding, R_text):
	CLS_idx = text_encoding.argmax(dim=-1)
	R_text = R_text[CLS_idx, 1:CLS_idx]
	text_scores = R_text / R_text.sum()
	text_scores = text_scores.flatten()
	print(text_scores)
	text_tokens = _tokenizer.encode(text)
	text_tokens_decoded = [_tokenizer.decode([a]) for a in text_tokens]
	vis_data_records = [visualization.VisualizationDataRecord(text_scores, 0, 0, 0, 0, 0, text_tokens_decoded, 1)]
	visualization.visualize_text(vis_data_records)


clip.clip._MODELS = {
	"ViT-B/32": "https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt",
	"ViT-B/16": "https://openaipublic.azureedge.net/clip/models/5806e77cd80f8b59890b7e101eabd078d9fb84e6937f9e85e4ecb61988df416f/ViT-B-16.pt",
	"ViT-L/14": "https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt",
}

class CLIPProcessor:
	def __init__(self,):

		self.device = "cuda" if torch.cuda.is_available() else "cpu"
		print("Loading CLIP...")
		self.model, self.preprocess = clip.load("ViT-B/32", device=self.device, jit=False)
		print("Finished loading.")

	def find_CLIP_similarity(self, texts: list, image: Image):
		img = self.preprocess(image).unsqueeze(0).to(self.device)
		text = clip.tokenize(texts).to(self.device)
		logits_per_image, logits_per_text, R_text, R_image = interpret(model=self.model, image=img, texts=text, device=self.device)
		text_batch_size = text.shape[0]
		for i in range(text_batch_size):
			# show_heatmap_on_text(texts[i], text[i], R_text[i])
			# show_image_relevance(R_image[i], img, orig_image=image)
			similarity_score = logits_per_image[i][0].item()
			vis = show_image_relevance(R_image[i], img, similarity_score)

			#text_vector = logits_per_text[i]

			# fig, axs = plt.subplots(1, 2)
			# axs[0].imshow(image)
			# axs[0].axis('off')
			# axs[1].imshow(vis)
			# axs[1].axis('off')
			#
			# plt.show()

			return vis, similarity_score



# def process_one():
# 	print('Your tex01t', flush=True)
# 	device = "cuda" if torch.cuda.is_available() else "cpu"
# 	print('Your tex111t', flush=True)
# 	model, preprocess = clip.load("ViT-B/32", device=device, jit=False)
# 	print('Your tex1t', flush=True)
#
# 	for _ in tqdm(range(150)):
# 		img_path = "TransformerExplainability/CLIP/DSC07509.jpg"
# 		img = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
# 		print('Your text4', flush=True)
# 		texts = ["a person wearing glasses"]
# 		text = clip.tokenize(texts).to(device)
# 		print('Your text2', flush=True)
# 		R_text, R_image = interpret(model=model, image=img, texts=text, device=device)
# 		batch_size = text.shape[0]
# 		print('Your text3', flush=True)
# 		# for i in range(batch_size):
# 		# 	show_heatmap_on_text(texts[i], text[i], R_text[i])
# 		# 	show_image_relevance(R_image[i], img, orig_image=Image.open(img_path))
# 		# 	plt.show()
# 	print('Your text', flush=True)


# thread = Thread(target=process_one, args=())
# thread.daemon = True
# thread.start()

#process_one()
