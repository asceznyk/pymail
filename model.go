package main

import (
  "context"
  "io/ioutil"
  "encoding/json"
  "log"
  "os"
  "golang.org/x/oauth2/google"
  "google.golang.org/api/gmail/v1"
  "google.golang.org/api/option"

  tea "github.com/charmbracelet/bubbletea"
  list "github.com/charmbracelet/bubbles/list"
)

type userConfig struct {
  Gmail string `json:"gmail"`
  Limit int `json:"limit"`
}

type messageTLDR struct {
  From string
  Subject string
}

func (m messageTLDR) FilterValue() string {
  return m.From
}

func (m messageTLDR) Title() string {
  return m.Subject
}

func (m messageTLDR) Description() string {
  return m.From
}

type Model struct {
  mails list.Model
  err error
}

func (m Model) Init() tea.Cmd {
  return nil
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) { 
  switch msg := msg.(type) {
  case tea.WindowSizeMsg:
    m.initList(msg.Width, msg.Height)
  }
  var cmd tea.Cmd
  m.mails, cmd = m.mails.Update(msg)
  return m, cmd
}

func (m Model) View() string {
  return m.mails.View()
}

func New() *Model {
  return &Model{}
}

func initService(configFile string, credFile string) (*gmail.Service, userConfig) {
  jsonFile, err := os.Open(configFile)
  if err != nil { log.Fatalf("%v", err) }
  defer jsonFile.Close()
  byteValue, _ := ioutil.ReadAll(jsonFile)
  var user userConfig = userConfig{}
  json.Unmarshal(byteValue, &user)
  ctx := context.Background()
  b, err := os.ReadFile(credFile)
  if err != nil { log.Fatalf("Unable to read client secret file: %v", err) }
  config, err := google.ConfigFromJSON(b, gmail.GmailReadonlyScope)
  if err != nil { log.Fatalf("Unable to parse client secret file to config: %v", err) }
  client := getClient(config)
  srv, err := gmail.NewService(ctx, option.WithHTTPClient(client))
  if err != nil { log.Fatalf("Unable to retrieve Gmail client: %v", err) } 
  return srv, user 
}

func getFilteredMessages(
  srv *gmail.Service, user userConfig, filter string,
) *gmail.ListMessagesResponse {
  r, err := srv.Users.Messages.List(user.Gmail).Q(filter).Do()
  if err != nil { log.Fatalf("Unable to retrieve messages: %v", err) }
  return r
}

func getMessageDetails(
  srv *gmail.Service, user userConfig, messageId string,
) messageTLDR {
  msg, err := srv.Users.Messages.Get(user.Gmail, messageId).Format("full").Do()
  if err != nil { log.Println("error when getting mail content: ", err) }
  var tldr messageTLDR = messageTLDR{}
  for _, head := range msg.Payload.Headers {
    if head.Name == "From" {tldr.From = head.Value }
    if head.Name == "Subject" { tldr.Subject = head.Value }
  }
  return tldr
}

func (m *Model) initList(width int, height int) {
  srv, user := initService("config.json", "credentials.json")
  r := getFilteredMessages(srv, user, "")
  m.mails = list.New([]list.Item{}, list.NewDefaultDelegate(), width, height)
  m.mails.Title = "Messages for " + user.Gmail
  var items []list.Item 
  for i, x := range r.Messages {
    if i >= user.Limit { break }
    tldr := getMessageDetails(srv, user, x.Id)
    items = append(items, tldr)
  }
  m.mails.SetItems(items)
}


