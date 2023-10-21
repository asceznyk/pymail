package main

import (
  "context"
  "fmt"
  "io/ioutil"
  "encoding/json"
  "log"
  "os"
  "golang.org/x/oauth2/google"
  "google.golang.org/api/gmail/v1"
  "google.golang.org/api/option"
)

func main() {
  jsonFile, err := os.Open("config.json")
  if err != nil { fmt.Println(err) }
  defer jsonFile.Close()
  byteValue, _ := ioutil.ReadAll(jsonFile)
  var user userConfig = userConfig{}
  json.Unmarshal(byteValue, &user)
  ctx := context.Background()
  b, err := os.ReadFile("credentials.json")
  if err != nil { log.Fatalf("Unable to read client secret file: %v", err) }
  config, err := google.ConfigFromJSON(b, gmail.GmailReadonlyScope)
  if err != nil { log.Fatalf("Unable to parse client secret file to config: %v", err) }
  client := getClient(config)
  srv, err := gmail.NewService(ctx, option.WithHTTPClient(client))
  if err != nil { log.Fatalf("Unable to retrieve Gmail client: %v", err) } 
  r := getFilteredMessages(srv, user.Gmail, "")
  fmt.Printf("Messages for %s - Limited to first %d mails:\n\n", user.Gmail, user.Limit)
  for i, m := range r.Messages {
    if i >= user.Limit { break }
    tldr := getMessageDetails(srv, user.Gmail, m.Id)
    fmt.Printf("%s -> %s \n\n", tldr.from, tldr.subject)
  }
}
