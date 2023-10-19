package main

import (
  "context"
  "encoding/json"
  "fmt"
  "log"
  "net/http"
  "os"
  "golang.org/x/oauth2"
  "golang.org/x/oauth2/google"
  "google.golang.org/api/gmail/v1"
  "google.golang.org/api/option"
  "encoding/base64"
)

func getClient(config *oauth2.Config) *http.Client {
  tokFile := "token.json"
  tok, err := tokenFromFile(tokFile)
  if err != nil {
    tok = getTokenFromWeb(config)
    saveToken(tokFile, tok)
  }
  return config.Client(context.Background(), tok)
}

func getTokenFromWeb(config *oauth2.Config) *oauth2.Token {
  authURL := config.AuthCodeURL("state-token", oauth2.AccessTypeOffline)
  fmt.Printf("Go to the following link in your browser then type the "+
  "authorization code: \n%v\n", authURL)
  var authCode string
  if _, err := fmt.Scan(&authCode); err != nil {
    log.Fatalf("Unable to read authorization code: %v", err)
  }
  tok, err := config.Exchange(context.TODO(), authCode)
  if err != nil {
    log.Fatalf("Unable to retrieve token from web: %v", err)
  }
  return tok
}

func tokenFromFile(file string) (*oauth2.Token, error) {
  f, err := os.Open(file)
  if err != nil {
    return nil, err
  }
  defer f.Close()
  tok := &oauth2.Token{}
  err = json.NewDecoder(f).Decode(tok)
  return tok, err
}

func saveToken(path string, token *oauth2.Token) {
  fmt.Printf("Saving credential file to: %s\n", path)
  f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
  if err != nil {
    log.Fatalf("Unable to cache oauth token: %v", err)
  }
  defer f.Close()
  json.NewEncoder(f).Encode(token)
}

func getMessageSubject(srv *gmail.Service, user string, messageId string) {
  msg, err := srv.Users.Messages.Get(user, messageId).Format("full").Do()
  if err != nil { 
    log.Println("error when getting mail content: ", err)
  }
  if msg == nil { return }
  fmt.Printf("%s\n", msg.Payload.Headers[19].Value)
}

func getMessageBody(srv *gmail.Service, user string, messageId string) {
  msg, err := srv.Users.Messages.Get(user, messageId).Format("full").Do()
  if err != nil { 
    log.Println("error when getting mail content: ", err)
  }
  if msg == nil { return }
  for i, part := range msg.Payload.Parts {
    fmt.Printf("part -> %d\n", i)
    content, _ := base64.URLEncoding.DecodeString(part.Body.Data)
    html := string(content)
    fmt.Printf("%s\n", html)
  }
  fmt.Println(messageId)
}

func main() {
  ctx := context.Background()
  emailID := os.Args[1:][0]
  b, err := os.ReadFile("credentials.json")
  if err != nil {
    log.Fatalf("Unable to read client secret file: %v", err)
  }
  config, err := google.ConfigFromJSON(b, gmail.GmailReadonlyScope)
  if err != nil {
    log.Fatalf("Unable to parse client secret file to config: %v", err)
  }
  client := getClient(config)
  srv, err := gmail.NewService(ctx, option.WithHTTPClient(client))
  if err != nil {
    log.Fatalf("Unable to retrieve Gmail client: %v", err)
  }
  user := "me"
  fmt.Println()
  r, err := srv.Users.Messages.List(user).Q(emailID).Do() 
  if err != nil {
    log.Fatalf("Unable to retrieve labels: %v", err)
  }
  if len(r.Messages) == 0 {
    fmt.Println("No messages found.")
    return
  }
  fmt.Println("Messages:")
  for i, m := range r.Messages {
    getMessageSubject(srv, user, m.Id)
    //getMessageBody(srv, user, m.Id)
    fmt.Println(i, emailID)
  }
}
