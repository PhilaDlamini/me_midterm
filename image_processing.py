cv2_image = cv2.cvtColor(np.array(cam.raw_image), cv2.COLOR_RGB2BGR)
b,g,r = cv2.split(cv2_image)
red = cv2.subtract(r,g)
green = cv2.subtract(g,r)
blue = cv2.subtract(b, r)

#apply blur 
blur_red = cv2.GaussianBlur(red, (5, 5), 0)
blur_blue = cv2.GaussianBlur(blue, (5, 5), 0)
blur_green = cv2.GaussianBlur(green, (5, 5), 0)

#threshold 
thresh_red = cv2.threshold(blur_red, 100, 255, cv2.THRESH_BINARY)[1]
thresh_green = cv2.threshold(blur_green, 100, 255, cv2.THRESH_BINARY)[1]
thresh_blue = cv2.threshold(blur_blue, 100, 255, cv2.THRESH_BINARY)[1]

#find countours 
cnts_red = cv2.findContours(thresh_red.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnts_blue = cv2.findContours(thresh_blue.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnts_green = cv2.findContours(thresh_green.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

#Find largest blob 
cnts_colors = [cnts_red[0], cnts_blue[0], cnts_green[0]]
areas = [0, 0, 0] #red, blue, green
colors = ['Red', 'Blue', 'Green']

for i in range(len(cnts_colors)):
    for c in cnts_colors[i]:
        areas[i] += cv2.contourArea(c)
largest_color = colors[np.argmax(areas)]
print('Largest color in image is', largest_color)


#Send color to Airtable using the MQTT
token = 'patbDnBxDqYjUCD8m.6c5194d260e2b1d692e46fb759db93e822eb8570409d13c4050ba861bccbe28b'
url = "https://api.airtable.com/v0/applFraZvr74IZXEL/Colors/recPoZwtOE2AmioZU"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {"fields" : {"Color": largest_color}}
response = requests.patch(url, headers=headers,json=payload)
print('Sent udpate to Airtable. Response:')
print(response.json())

