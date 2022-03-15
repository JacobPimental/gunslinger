from gunslinger import Gunslinger

def lambda_handler(event, context):
    print("Let's get this shit going!!!!")
    gunslinger = Gunslinger()
    gunslinger.parse_message(event)

if __name__ == '__main__':
    gunslinger = Gunslinger()
    gunslinger.parse_message({
        "processor": "urlscan_processor",
        "data": [
            "https://urlscan.io/api/v1/result/7e9b3d00-22f0-4bfb-8d91-e2c74a044be6/"
            ]
    })
